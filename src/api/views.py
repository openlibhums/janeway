import collections
import csv
import io
import json
import re

from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Q

from rest_framework import viewsets, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions

from api import serializers, permissions as api_permissions
from core import models as core_models
from submission import models as submission_models
from journal import models as journal_models


@api_view(['GET'])
@permission_classes((permissions.AllowAny, ))
def index(request):
    response_dict = {
        'Message': 'Welcome to the API',
        'Version': '1.0',
        'API Endpoints':
            [],
    }
    json_content = json.dumps(response_dict)

    return HttpResponse(json_content, content_type="application/json")


@permission_classes((permissions.IsAdminUser,))
class AccountViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows staff to see user accounts.
    """
    serializer_class = serializers.AccountSerializer

    def get_queryset(self):
        """
        Optionally restricts the returned object to a given user,
        by filtering against a `email` query parameter in the URL.
        """
        queryset = core_models.Account.objects.all()
        search = self.request.query_params.get('search')
        escaped = re.escape(search)
        split_term = [re.escape(word) for word in search.split(" ")]
        split_term.append(escaped)
        search_regex = "^({})$".format(
            "|".join({name for name in split_term})
        )

        if search is not None:
            queryset = queryset.filter(
                Q(email__icontains=search) |
                Q(first_name__iregex=search_regex) |
                Q(last_name__iregex=search_regex)
            )
        return queryset


@permission_classes((api_permissions.IsEditor, ))
class AccountRoleViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows user roles to be viewed or edited.
    """
    queryset = core_models.AccountRole.objects.filter()
    serializer_class = serializers.AccountRoleSerializer


class JournalViewSet(viewsets.ModelViewSet):
    """
    API Endpoint for journals.
    """
    from journal import models as journal_models
    queryset = journal_models.Journal.objects.filter(hide_from_press=False)
    serializer_class = serializers.JournalSerializer
    http_method_names = ['get']


class IssueViewSet(viewsets.ModelViewSet):
    """
    API Endpoint for journals.
    """
    serializer_class = serializers.IssueSerializer
    http_method_names = ['get']

    def get_queryset(self):
        from journal import models as journal_models
        if self.request.journal:
            queryset = journal_models.Issue.objects.filter(journal=self.request.journal)
        else:
            queryset = journal_models.Issue.objects.all()

        return queryset


class LicenceViewSet(viewsets.ModelViewSet):
    """
    API Endpoint for journals.
    """
    serializer_class = serializers.LicenceSerializer
    http_method_names = ['get']

    def get_queryset(self):

        if self.request.journal:
            queryset = submission_models.Licence.objects.filter(journal=self.request.journal)
        else:
            queryset = submission_models.Licence.objects.filter(journal=self.request.press)

        return queryset


class KeywordsViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.KeywordsSerializer
    queryset = submission_models.Keyword.objects.all()
    http_method_names = ['get']


class ArticleViewSet(viewsets.ModelViewSet):
    """
    API Endpoint for journals.
    """
    serializer_class = serializers.ArticleSerializer
    http_method_names = ['get']

    def get_queryset(self):
        if self.request.journal:
            queryset = submission_models.Article.objects.filter(journal=self.request.journal,
                                                                stage=submission_models.STAGE_PUBLISHED,
                                                                date_published__lte=timezone.now())
        else:
            queryset = submission_models.Article.objects.filter(stage=submission_models.STAGE_PUBLISHED,
                                                                date_published__lte=timezone.now())

        return queryset


def oai(request):
    articles = submission_models.Article.objects.filter(stage=submission_models.STAGE_PUBLISHED)
    if request.journal:
        articles = articles.filter(journal=request.journal)

    template = 'apis/OAI.xml'
    context = {
        'articles': articles,
    }

    return render(request, template, context, content_type="application/xml")


def kbart_csv(request):
    return kbart(request, tsv=False)


def kbart(request, tsv=True):
    """
    Produces KBART metadata output according to the spec:
    https://doi.org/10.1080/0361526X.2017.1309826
    @param request: the request object
    @param tsv: whether to produce a TSV file. If False then renders a CSV
    @return: a rendered CSV or TSV
    """

    # establish if we are outputting TSV or CSV
    delimiter = '\t' if tsv else ','

    response = HttpResponse(content_type='text/csv') if delimiter == ',' \
        else HttpResponse(content_type='text/tsv')

    response['Content-Disposition'] = 'attachment; filename="kbart.csv"' \
        if delimiter == ',' else 'attachment; filename="kbart.tsv"'

    # header and stream objects
    has_header = False
    writer = None

    for journal in journal_models.Journal.objects.filter(is_remote=False, hide_from_press=False):
        kbart_embargo = journal.get_setting(
            'kbart', 'embargo_period')
        # Note that we here use an OrderedDict. This is important as the
        # field headers are generated below at the late init of the TSV or
        # CSV writer and need to be in the right order. Hence, fields should
        # be correctly ordered below.
        journal_line = collections.OrderedDict()

        journal_line['publication_title'] = journal.name
        journal_line['online_identifier'] = journal.issn
        journal_line['print_identifier'] = journal.print_issn

        issues = journal.serial_issues().filter(
            date__lte=timezone.now().date(),
        ).order_by("date")

        # We here iterate over the issues.
        # Technically, this should check if issues are consecutive
        # because we should specify full date ranges for only material that
        # we definitely hold. A future revision to this code could check
        # that a whole issue is not purely composed of remote galley
        # articles and exclude that issue.
        if issues.exists():
            first_issue = issues.first()
            last_issue = issues.last()
            # the date that the first issue that we have was published
            journal_line['date_first_issue_online'] = '{:%Y-%m-%d}'.format(
                first_issue.date)

            # the volume number of the first issue that we have
            journal_line['num_first_vol_online'] = first_issue.volume

            # the issue number of the first issue that we have
            journal_line['num_first_issue_online'] = first_issue.issue

            # The date that the last issue that we have was published,
            # this is should only be populated if the article has ceased
            # publication OR if the article  publishes content after a
            # period of embargo
            if journal.is_archived or kbart_embargo:
                journal_line['date_last_issue_online'] = '{:%Y-%m-%d}'.format(
                    last_issue.date)
                # the issue number of the last issue that we have
                journal_line['num_last_issue_online'] = last_issue.issue
                # the volume number of the last issue that we have
                journal_line['num_last_vol_online'] = last_issue.volume
            else:
                journal_line['date_last_issue_online'] = None
                journal_line['num_last_issue_online'] = None
                journal_line['num_last_vol_online'] = None


        else:
            # set these fields to None if there are no issues
            journal_line['date_first_issue_online'] = None
            journal_line['num_first_vol_online'] = None
            journal_line['num_first_issue_online'] = None
            journal_line['date_last_issue_online'] = None
            journal_line['num_last_vol_online'] = None
            journal_line['num_last_issue_online'] = None

        # the url of the journal
        journal_line['title_url'] = journal.site_url()

        # the first author of a monograph
        journal_line['first_author'] = None # only for monographs (OFM)

        # the issn of the journal
        journal_line['title_id'] = journal.issn

        # Applicable to journals that publish in print but have period of 
        # embargo period before publishing online
        journal_line['embargo_info'] = kbart_embargo or None

        # the type of coverage that we have available
        journal_line['coverage_depth'] = 'fulltext'

        # a notes field for giving additional information
        journal_line['notes'] = None # not needed

        # the name of the publisher which can be specific to the journal
        journal_line['publisher_name'] = journal.get_setting(
            'general', 'publisher_name')

        # the type of publication: either monograph or serial
        # because we have prefiltered, we only list serials here
        journal_line['publication_type'] = 'serial'

        # for monographs, the print and online publication dates
        journal_line['date_monograph_published_print'] = None # OFM
        journal_line['date_monograph_published_online'] = None # OFM

        # the monograph volume and edition
        journal_line['monograph_volume'] = None # OFM
        journal_line['monograph_edition'] = None # OFM

        # the first editor of a monograph
        journal_line['first_editor'] = None # OFM

        # this is a way of presenting the history of a title if it has
        # changed publisher hands etc.
        # we do not record this information in Janeway at present but it
        # may be useful information to store in future
        # TODO: record journal history of ISSN
        journal_line['parent_publication_title_id'] = None # not needed
        journal_line['preceding_publication_title_id'] = None # not needed

        # from the spec: "The access_type field is used to indicate whether
        # a publication is fee-based or Open Access.T his field has only two
        # possible values: F (free) or P (paid). F should be used only if
        # 100% of the content being described is free. If a title has a mix
        # of paid and free content, the P value should be used. If a title
        # has a mix of free and paid content that is clearly delineated by
        # volume, multiple lines can be included within a KBART file to
        # indicate the coverage ranges for each type of access."
        journal_line['access_type'] = 'F'

        if not has_header:
            # init the streamwriter and write the header
            writer = csv.DictWriter(response,
                                    fieldnames=journal_line.keys(),
                                    delimiter=delimiter)
            has_header = True
            writer.writeheader()

        writer.writerow(journal_line)

    return response
