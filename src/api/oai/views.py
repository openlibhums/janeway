"""
A django implementation of the OAI-PMH interface
"""
from django.utils import timezone
from django.views.generic.base import TemplateView

from api.oai import exceptions
from api.oai.base import OAIPagedModelView, metadata_formats
from identifiers.models import Identifier
from submission import models as submission_models
from repository import models as repo_models
from utils.upgrade import shared
from journal import models as journal_models
from xml.dom import minidom

# We default `verb` to ListRecords for backwards compatibility.
DEFAULT_ENDPOINT = "ListRecords"
DEFAULT_METADATA_PREFIX = 'oai_dc'


def oai_view_factory(request, *args, **kwargs):
    """ Maps an incoming OAI request to a django CB view
    The OAI protocol uses a querystring parameter (verb) to determine
    the resource being queried. This is not supported by Django's URL
    router, so we do our own mapping here and pass this factory to the
    url constructor instead of a view. As a result, all the OAI endpoints
    will have the same django view name.
    """
    try:
        verb = request.GET.get("verb")
        if verb is None:
            verb = DEFAULT_ENDPOINT
        elif verb not in ROUTES:
            raise exceptions.OAIBadVerb()
        if request.repository:
            view = PREPRINT_ROUTES.get(verb)
        else:
            view = ROUTES.get(verb)
        return view(request, *args, **kwargs)
    except exceptions.OAIException as oai_error:
        return OAIErrorResponse.as_view(error=oai_error)(request)


class OAIListRecords(OAIPagedModelView):

    # default is OAI_DC
    template_name = "apis/OAI_ListRecords.xml"
    queryset = submission_models.Article.objects.all()
    paginate_by = 50

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.request.journal:
            queryset = queryset.filter(journal=self.request.journal)
        else:
            queryset = queryset.filter(journal__hide_from_press=False)
        set_filter = self.request.GET.get('set')
        issue_type_list = [issue_type.code for issue_type in journal_models.IssueType.objects.all()]

        if set_filter:
            filter_parts = set_filter.split(":")

            # Currently set will either equal a journal code or include a
            # journal code, issue_type and pk or journal_code, section and pk
            if len(filter_parts) == 1 and not self.request.journal:
                # We have not current journal and have a journal filter.
                queryset = queryset.filter(
                    journal__code=filter_parts[0],
                )
            elif len(filter_parts) == 3:
                # We have either an issue or a section
                if filter_parts[1] in issue_type_list:
                    # Issue/Collection
                    try:
                        issue = journal_models.Issue.objects.get(
                            journal__code=self.request.journal.code if self.request.journal else filter_parts[0],
                            pk=filter_parts[2]
                        )
                        queryset = issue.articles.filter(
                            date_published__isnull=False,
                        )
                    except journal_models.Issue.DoesNotExist:
                        queryset = submission_models.Article.objects.none()
                elif filter_parts[1] == 'section':
                    # Section
                    queryset = queryset.filter(
                        section__pk=filter_parts[2],
                    )
                else:
                    queryset = submission_models.Article.objects.none()

        return queryset

    def filter_by_journal(self, qs):
        if self.request.journal:
            return qs.filter(journal=self.request.journal)
        return qs

    def filter_is_published(self, qs):
        return qs.filter(
            stage=submission_models.STAGE_PUBLISHED,
            date_published__lte=timezone.now(),
        )

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["verb"] = self.request.GET.get("verb", DEFAULT_ENDPOINT)
        context["metadataPrefix"] = self.request.GET.get("metadataPrefix", DEFAULT_METADATA_PREFIX)
        return context


class OAIGetRecord(TemplateView):
    template_name = "apis/OAI_GetRecord.xml"
    content_type = "application/xml"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["article"] = self.get_article()
        context["verb"] = self.request.GET.get("verb")
        context["metadataPrefix"] = self.request.GET.get("metadataPrefix", DEFAULT_METADATA_PREFIX)
        context["jats"], context["stub"] = self.get_jats(context["article"])
        return context

    def get_jats(self, article):
        """
        Fetches either JATS from the article or a stub
        @param article: the article on which to operate
        @return: JATS XML or a metadata stub, True or False for whether this is
        a stub (False = full JATS, True = stub only)
        """
        render_galley = article.get_render_galley

        # check if this is a JATS XML file
        try:
            if render_galley:
                with open(render_galley.file.get_file_path(article),
                          'r') as galley:
                    contents = galley.read()

                    if 'DTD JATS' in contents:
                        # assume this is a JATS XML file
                        # we need to strip the XML header, though
                        domified_xml = minidom.parseString(contents)
                        return domified_xml.documentElement.toxml('utf-8'), \
                               False
        except:
            # a broad catch that lets us generate a stub if anything goes wrong
            pass

        return None, True

    def get_article(self):
        id_param = self.request.GET.get("identifier")
        try:
           _, site_code, id_type, identifier = id_param.split(":")
        except (ValueError, AttributeError):
            raise exceptions.OAIBadArgument()

        try:
            if id_type == "id":
                article = submission_models.Article.objects.get(
                    id=identifier,
                    stage=submission_models.STAGE_PUBLISHED,
                )
            else:
                article = Identifier.objects.get(
                    id_type=id_type, identifier=identifier,
                    article__stage=submission_models.STAGE_PUBLISHED,
                ).article
        except (
            Identifier.DoesNotExist,
            submission_models.Article.DoesNotExist,
        ):
            raise exceptions.OAIDoesNotExist()

        return article


class OAIListIdentifiers(OAIListRecords):
    template_name = "apis/OAI_ListIdentifiers.xml"


class OAIListMetadataFormats(TemplateView):
    template_name = 'apis/OAI_ListMetadataFormats.xml'
    content_type = 'application/xml'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["metadata_formats"] = metadata_formats
        context["verb"] = self.request.GET.get("verb")
        context["metadataPrefix"] = self.request.GET.get("metadataPrefix", DEFAULT_METADATA_PREFIX)
        return context


class OAIIdentify(TemplateView):
    template_name = "apis/OAI_Identify.xml"
    content_type = "application/xml"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['version'] = shared.current_version()

        articles = submission_models.Article.objects.all()

        if self.request.journal:
            articles = articles.filter(
                journal=self.request.journal,
                stage=submission_models.STAGE_PUBLISHED,
            )

        context['earliest_article'] = articles.earliest('date_published')
        context["verb"] = self.request.GET.get("verb")
        context["metadataPrefix"] = self.request.GET.get("metadataPrefix", DEFAULT_METADATA_PREFIX)

        return context


class OAIListSets(TemplateView):
    template_name = "apis/OAI_ListSets.xml"
    content_type = "application/xml"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        journals = journal_models.Journal.objects.all()
        all_issues = journal_models.Issue.objects.all()
        sections = submission_models.Section.objects.all()

        if self.request.journal:
            journals = journals.filter(
                code=self.request.journal.code,
            )
            all_issues = all_issues.filter(
                journal=self.request.journal,
            )
            sections = sections.filter(
                journal=self.request.journal,
            )

        context['journals'] = journals
        context['all_issues'] = all_issues
        context['sections'] = sections
        context["verb"] = self.request.GET.get("verb")
        context["metadataPrefix"] = self.request.GET.get("metadataPrefix", DEFAULT_METADATA_PREFIX)

        return context


class OAIErrorResponse(TemplateView):
    """ Base Error response returned for raised OAI API errors

    Children should implement `error` as an instance of a OAIException.
    Dynamic resposne types can be generated by passing the `error` as an
    initkwarg to `OAIErrorResponse.as_view(**initkwargs)` as per django docs
    """
    template_name = "apis/OAI_error.xml"
    content_type = "application/xml"
    error = None

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["error"] = self.error
        return context


class OAIListPreprintRecords(OAIPagedModelView):
    template_name = "apis/OAI_ListRecords.xml"
    queryset = repo_models.Preprint.objects.all()
    paginate_by = 50

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.request.repository:
            queryset = queryset.filter(repository=self.request.repository).order_by('date_published')
        return queryset

    def filter_is_published(self, qs):
        return qs.filter(
            stage=submission_models.STAGE_PREPRINT_PUBLISHED,
            date_published__lte=timezone.now(),
        )

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["verb"] = self.request.GET.get("verb", DEFAULT_ENDPOINT)
        context["metadataPrefix"] = self.request.GET.get("metadataPrefix", DEFAULT_METADATA_PREFIX)
        context["is_preprints"] = self.request.repository
        return context

class OAIGetPreprintRecord(OAIGetRecord):
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["is_preprints"] = self.request.repository
        return context

    def get_jats(self, article):
        return None, True

    def get_article(self):
        id_param = self.request.GET.get("identifier")
        try:
           _, site_code, id_type, identifier = id_param.split(":")
        except (ValueError, AttributeError):
            raise exceptions.OAIBadArgument()

        try:
            article = repo_models.Preprint.objects.get(
                id=identifier,
                stage=repo_models.STAGE_PREPRINT_PUBLISHED,
            )
        except (
            Identifier.DoesNotExist,
            submission_models.Article.DoesNotExist,
        ):
            raise exceptions.OAIDoesNotExist()

        return article

class OAIListPreprintIdentifiers(OAIListPreprintRecords):
    template_name = "apis/OAI_ListIdentifiers.xml"

class OAIPreprintIdentify(TemplateView):
    template_name = "apis/OAI_PreprintIdentify.xml"
    content_type = "application/xml"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['version'] = shared.current_version()

        articles = repo_models.Preprint.objects.all()

        if self.request.repository:
            articles = articles.filter(
                repository=self.request.repository,
                stage=submission_models.STAGE_PREPRINT_PUBLISHED,
            )

        context['earliest_article'] = articles.earliest('date_published')
        context["verb"] = self.request.GET.get("verb")
        context["metadataPrefix"] = self.request.GET.get("metadataPrefix", DEFAULT_METADATA_PREFIX)

        return context

class OAIListPreprintSets(TemplateView):
    template_name = "apis/OAI_ListSets.xml"
    content_type = "application/xml"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        context["verb"] = self.request.GET.get("verb")
        context["metadataPrefix"] = self.request.GET.get("metadataPrefix", DEFAULT_METADATA_PREFIX)

        return context

PREPRINT_ROUTES = {
    "GetRecord": OAIGetPreprintRecord.as_view(),
    "ListRecords": OAIListPreprintRecords.as_view(),
    "ListIdentifiers": OAIListPreprintIdentifiers.as_view(),
    "ListMetadataFormats": OAIListMetadataFormats.as_view(),
    "Identify": OAIPreprintIdentify.as_view(),
    "ListSets": OAIListPreprintSets.as_view(),
}

ROUTES = {
    "GetRecord": OAIGetRecord.as_view(),
    "ListRecords": OAIListRecords.as_view(),
    "ListIdentifiers": OAIListIdentifiers.as_view(),
    "ListMetadataFormats": OAIListMetadataFormats.as_view(),
    "Identify": OAIIdentify.as_view(),
    "ListSets": OAIListSets.as_view(),
}
