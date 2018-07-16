__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django.shortcuts import render, redirect
from django.urls import reverse
from django.core.management import call_command

from submission import models
from identifiers import models as ident_models
from security.decorators import editor_user_required
from metrics import logic


@editor_user_required
def index(request):
    """
    Displays a list of reports.
    :param request: HttpRequest object
    :return: HttpResponse
    """
    template = 'reports/index.html'
    context = {}

    return render(request, template, context)


@editor_user_required
def metrics(request):
    """
    Displays paginated list of articles and their metrics.
    :param request: HttpRequest object
    :return: HttpResponse
    """
    articles = models.Article.objects.filter(journal=request.journal,
                                             stage=models.STAGE_PUBLISHED)

    total_views, total_downs = logic.get_view_and_download_totals(articles)

    template = 'reports/metrics.html'
    context = {
        'articles': articles,
        'total_views': total_views,
        'total_downs': total_downs,
    }

    return render(request, template, context)


@editor_user_required
def dois(request):
    """
    Displays a list of BrokenDOI objects.
    :param request: HttpRequest object
    :return: HttpResponse object
    """
    broken_dois = ident_models.BrokenDOI.objects.filter(article__journal=request.journal)

    if request.POST and 'run' in request.POST:
        call_command('doi_check')
        return redirect(reverse('reports_dois', request.journal.code))

    template = 'reports/dois.html'
    context = {
        'broken_dois': broken_dois,
    }

    return render(request, template, context)
