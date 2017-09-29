__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.shortcuts import render
from django.utils import timezone

from submission import models as submission_models

def preprints_home(request):

    preprints = submission_models.Article.preprints.filter(
        date_published__lte=timezone.now()).order_by('-date_published')[:6]

    template = 'preprints/home.html'
    context = {
        'preprints': preprints,
    }

    return render(request, template, context)


def preprints_about(request):

    template = 'preprints/about.html'
    context = {

    }

    return render(request, template, context)