__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import operator
from functools import reduce

from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.db.models import Q
from django.urls import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from submission import models as submission_models
from core import models as core_models


def preprints_home(request):
    """
    Displays the preprints home page with search box and 6 latest preprint publications
    :param request: HttpRequest object
    :return: HttpResponse
    """
    preprints = submission_models.Article.preprints.filter(
        date_published__lte=timezone.now()).order_by('-date_published')[:6]

    template = 'preprints/home.html'
    context = {
        'preprints': preprints,
    }

    return render(request, template, context)


def preprints_about(request):
    """
    Displays the about page with text about preprints
    :param request: HttpRequest object
    :return: HttpResponse
    """
    template = 'preprints/about.html'
    context = {

    }

    return render(request, template, context)


def preprints_search(request, search_term=None):
    """
    Searches through preprints based on their titles and authors
    :param request: HttpRequest
    :param search_term: Optional string
    :return: HttpResponse
    """
    if search_term:
        split_search_term = search_term.split(' ')

        article_search = submission_models.Article.preprints.filter(
            (Q(title__icontains=search_term) |
             Q(subtitle__icontains=search_term) |
             Q(keywords__word__in=split_search_term))
        )
        article_search = [article for article in article_search]

        institution_query = reduce(operator.and_, (Q(institution__icontains=x) for x in split_search_term))

        from_author = core_models.Account.objects.filter(
            (Q(first_name__in=split_search_term) |
             Q(last_name__in=split_search_term) |
             institution_query)
        )

        articles_from_author = [article for article in submission_models.Article.preprints.filter(
            authors__in=from_author)]
        articles = set(article_search + articles_from_author)

    else:
        articles = submission_models.Article.preprints.all()

    if request.POST:
        search_term = request.POST.get('search_term')
        return redirect(reverse('preprints_search_with_term', kwargs={'search_term': search_term}))

    paginator = Paginator(articles, 15)
    page = request.GET.get('page', 1)

    try:
        articles = paginator.page(page)
    except PageNotAnInteger:
        articles = paginator.page(1)
    except EmptyPage:
        articles = paginator.page(paginator.num_pages)

    template = 'preprints/search.html'
    context = {
        'search_term': search_term,
        'articles': articles,
    }

    return render(request, template, context)


def preprints_article(request, article_id):
    """
    Fetches a single article and displays its metadata
    :param request: HttpRequest
    :param article_id: integer, PK of an Article object
    :return: HttpResponse or Http404 if object not found
    """
    article = get_object_or_404(submission_models.Article.preprints.prefetch_related('authors'), pk=article_id,
                                stage=submission_models.STAGE_PUBLISHED,
                                date_published__lte=timezone.now())

    try:
        pdf = article.galley_set.get(type='pdf')
    except core_models.Galley.DoesNotExist:
        pdf = None

    template = 'preprints/article.html'
    context = {
        'article': article,
        'galleys': article.galley_set.all(),
        'pdf': pdf,
    }

    return render(request, template, context)


def preprints_pdf(request, article_id):

    pdf_url = request.GET.get('file')

    template = 'preprints/pdf.html'
    context = {
        'pdf_url': pdf_url,
    }
    return render(request, template, context)