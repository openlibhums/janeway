__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django.shortcuts import render

from submission import models


def index(request):

    template = 'reports/index.html'
    context = {}

    return render(request, template, context)


def metrics(request):

    articles = models.Article.objects.filter(journal=request.journal, stage=models.STAGE_PUBLISHED)

    template = 'reports/metrics.html'
    context = {
        'articles': articles,
    }

    return render(request, template, context)