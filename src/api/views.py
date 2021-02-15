import csv
import io
import json

from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from rest_framework import viewsets, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions

from api import serializers, permissions as api_permissions
from core import models as core_models
from submission import models as submission_models


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


def kbart(request):
    """
    Produces KBART metadata output
    @param request: the request object
    @return: a rendered CSV
    """
    fields = ["date_first_issue_online", "num_first_vol_online", "num_first_issue_online", "date_last_issue_online",
              "num_last_vol_online", "num_last_issue_online", "title_url", "first_author", "title_id", "embargo_info",
              "coverage_depth", "notes", "publisher_name", "publication_type", "date_monograph_published_print",
              "date_monograph_published_online", "monograph_volume", "monograph_edition", "first_editor",
              "parent_publication_title_id", "preceding_publication_title_id", "access_type"]

    response = HttpResponse(content_type='text/csv')
    writer = csv.DictWriter(response, fieldnames=fields)

    writer.writeheader()

    for journal in request.press.journals():
        journal_line = {}
        issues = journal.issues()
        if issues.count() > 0:
            journal_line['date_first_issue_online'] = '{:%Y-%m-%d}'.format(issues.order_by('date')[0].date)
            journal_line['num_first_vol_online'] = issues.order_by('date')[0].volume
            journal_line['num_first_issue_online'] = issues.order_by('date')[0].issue
            journal_line['date_last_issue_online'] = '{:%Y-%m-%d}'.format(issues.order_by('-date')[0].date)
            journal_line['num_last_vol_online'] = issues.order_by('-date')[0].volume
            journal_line['num_last_issue_online'] = issues.order_by('-date')[0].issue

        journal_line['title_url'] = journal.full_url()
        journal_line['coverage_depth'] = 'fulltext'
        journal_line['publisher_name'] = request.press.name
        journal_line['publication_type'] = 'serial'
        journal_line['title_id'] = journal.issn
        journal_line['access_type'] = 'F'

        writer.writerow(journal_line)

    response['Content-Disposition'] = 'attachment; filename="kbart.csv"'

    return response
