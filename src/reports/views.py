__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django.shortcuts import render
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

from submission import models


def index(request):

    template = 'reports/index.html'
    context = {}

    return render(request, template, context)


def metrics(request):

    articles = models.Article.objects.filter(journal=request.journal, stage=models.STAGE_PUBLISHED)
    paginator = Paginator(articles, 25)

    page = request.GET.get('page')
    try:
        articles = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        articles = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        articles = paginator.page(paginator.num_pages)

    template = 'reports/metrics.html'
    context = {
        'articles': articles,
    }

    return render(request, template, context)