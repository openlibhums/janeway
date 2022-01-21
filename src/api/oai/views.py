"""
A django implementation of the OAI-PMH interface
"""
from django.utils import timezone
from django.views.generic.base import TemplateView

from api.oai import exceptions
from api.oai.base import OAIPagedModelView, metadata_formats
from identifiers.models import Identifier
from submission import models as submission_models
from xml.dom import minidom

# We default `verb` to ListRecords for backwards compatibility.
DEFAULT_ENDPOINT = "ListRecords"


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
        view = ROUTES.get(verb)
        return view(request, *args, **kwargs)
    except exceptions.OAIException as oai_error:
        return OAIErrorResponse.as_view(error=oai_error)(request)


class OAIListRecords(OAIPagedModelView):

    # default is OAI_DC
    template_name = "apis/OAI_ListRecords.xml"
    queryset = submission_models.Article.objects.all()
    paginate_by = 50

    def get_template_names(self):
        """
        This is the ridiculous way that you have to override template
        selection in CBVs
        @return: the correct template
        """
        if self.request.GET.get('metadataPrefix') == 'oai_jats':
            # OAI_JATS output
            return "apis/OAI_ListRecordsJats.xml"
        else:
            # default to OAI_DC
            return "apis/OAI_ListRecords.xml"

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
        context["verb"] = self.request.GET.get("verb")
        context["metadataPrefix"] = self.request.GET.get("metadataPrefix")
        return context


class OAIGetRecord(TemplateView):
    template_name = "apis/OAI_GetRecord.xml"
    content_type = "application/xml"

    def get_template_names(self):
        """
        This is the ridiculous way that you have to override template
        selection in CBVs
        @return: the correct template
        """
        if self.request.GET.get('metadataPrefix') == 'oai_jats':
            # OAI_JATS output
            return "apis/OAI_GetRecordJats.xml"
        else:
            # default to OAI_DC
            return "apis/OAI_GetRecord.xml"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["article"] = self.get_article()
        context["verb"] = self.request.GET.get("verb")
        context["metadataPrefix"] = self.request.GET.get("metadataPrefix")
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
            id_type, id = id_param.split(":")
        except (ValueError, AttributeError):
            raise exceptions.OAIBadArgument()

        try:
            if id_type == "id":
                article = submission_models.Article.objects.get(
                    id=id,
                    stage=submission_models.STAGE_PUBLISHED,
                )
            else:
                article = Identifier.objects.get(
                    id_type=id_type, identifier=id,
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
        context["metadataPrefix"] = self.request.GET.get("metadataPrefix")
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


ROUTES = {
    "GetRecord": OAIGetRecord.as_view(),
    "ListRecords": OAIListRecords.as_view(),
    "ListIdentifiers": OAIListIdentifiers.as_view(),
    "ListMetadataFormats": OAIListMetadataFormats.as_view(),
}
