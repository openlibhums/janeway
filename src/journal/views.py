__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import json
import re

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.urls import reverse
from django.db import IntegrityError
from django.db.models import Q, Count
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.management import call_command

from cms import models as cms_models
from core import (
    files,
    models as core_models,
    plugin_loader,
    logic as core_logic,
)
from journal import logic, models, issue_forms, forms, decorators
from journal.logic import get_galley_content
from metrics.logic import store_article_access
from review import forms as review_forms
from security.decorators import article_stage_accepted_or_later_required, \
    article_stage_accepted_or_later_or_staff_required, article_exists, file_user_required, has_request, has_journal, \
    file_history_user_required, file_edit_user_required, production_user_or_editor_required, \
    editor_user_required, keyword_page_enabled
from submission import models as submission_models
from utils import models as utils_models, shared
from utils.logger import get_logger
from events import logic as event_logic

logger = get_logger(__name__)


@has_journal
@decorators.frontend_enabled
def home(request):
    """ Renders a journal homepage.

    :param request: the request associated with this call
    :return: a rendered template of the journal homepage
    """
    issues_objects = models.Issue.objects.filter(journal=request.journal)
    sections = submission_models.Section.objects.filter(
        journal=request.journal,
    )

    homepage_elements, homepage_element_names = core_logic.get_homepage_elements(
        request,
    )

    template = 'journal/index.html'
    context = {
        'homepage_elements': homepage_elements,
        'issues': issues_objects,
        'sections': sections,
    }

    # call all registered plugin block hooks to get relevant contexts

    for hook in settings.PLUGIN_HOOKS.get('yield_homepage_element_context', []):
        if hook.get('name') in homepage_element_names:
            try:
                hook_module = plugin_loader.import_module(hook.get('module'))
                function = getattr(hook_module, hook.get('function'))
                element_context = function(request, homepage_elements)

                for k, v in element_context.items():
                    context[k] = v
            except utils_models.Plugin.DoesNotExist as e:
                if settings.DEBUG:
                    logger.debug(e)
                else:
                    pass

    return render(request, template, context)


@has_journal
def serve_journal_cover(request):
    """ Serves the cover image for this journal or, if not affiliated with a journal, serves the press logo.

    :param request: the request associated with this call
    :return: a streaming response of the retrieved image file
    """
    if not request.journal:
        # URL accessed from press site so serve press cover
        response = files.serve_press_cover(request, request.press.thumbnail_image)

        return response

    if not request.journal.thumbnail_image:
        logic.install_cover(request.journal, request)

    response = files.serve_journal_cover(request, request.journal.thumbnail_image)

    return response


@has_journal
def funder_articles(request, funder_id):
    """ Renders the list of articles in the journal.

        :param request: the request associated with this call
        :return: a rendered template of all articles
        """
    if request.POST and 'clear' in request.POST:
        return logic.unset_article_session_variables(request)

    sections = submission_models.Section.objects.language().fallbacks(
        'en'
    ).filter(
        journal=request.journal,
        is_filterable=True,
    )
    page, show, filters, sort, redirect, active_filters = logic.handle_article_controls(request, sections)

    if redirect:
        return redirect

    pinned_articles = [pin.article for pin in models.PinnedArticle.objects.filter(
        journal=request.journal)]
    pinned_article_pks = [article.pk for article in pinned_articles]

    article_objects = submission_models.Article.objects.filter(
        journal=request.journal,
        funders__fundref_id=funder_id,
        date_published__lte=timezone.now(),
        section__pk__in=filters,
    ).prefetch_related(
        'frozenauthor_set').order_by(sort).exclude(
        pk__in=pinned_article_pks)

    paginator = Paginator(article_objects, show)

    try:
        articles = paginator.page(page)
    except PageNotAnInteger:
        articles = paginator.page(1)
    except EmptyPage:
        articles = paginator.page(paginator.num_pages)

    template = 'journal/articles.html'
    context = {
        'pinned_articles': pinned_articles,
        'articles': articles,
        'sections': sections,
        'filters': filters,
        'sort': sort,
        'show': show,
        'active_filters': active_filters,
        'search_form': forms.SearchForm(),
    }
    return render(request, template, context)


@has_journal
@decorators.frontend_enabled
def articles(request):
    """ Renders the list of articles in the journal.

    :param request: the request associated with this call
    :return: a rendered template of all articles
    """
    if request.POST and 'clear' in request.POST:
        return logic.unset_article_session_variables(request)

    sections = submission_models.Section.objects.language().fallbacks('en').filter(journal=request.journal,
                                                                                   is_filterable=True)
    page, show, filters, sort, redirect, active_filters = logic.handle_article_controls(request, sections)

    if redirect:
        return redirect

    pinned_articles = [pin.article for pin in models.PinnedArticle.objects.filter(
        journal=request.journal)]
    pinned_article_pks = [article.pk for article in pinned_articles]

    article_objects = submission_models.Article.objects.filter(
        journal=request.journal,
        stage=submission_models.STAGE_PUBLISHED,
        date_published__lte=timezone.now(),
        section__pk__in=filters,
    ).prefetch_related(
        'frozenauthor_set',
    ).order_by(sort).exclude(
        pk__in=pinned_article_pks,
    )

    paginator = Paginator(article_objects, show)

    try:
        articles = paginator.page(page)
    except PageNotAnInteger:
        articles = paginator.page(1)
    except EmptyPage:
        articles = paginator.page(paginator.num_pages)

    template = 'journal/articles.html'
    context = {
        'pinned_articles': pinned_articles,
        'articles': articles,
        'sections': sections,
        'filters': filters,
        'sort': sort,
        'show': show,
        'active_filters': active_filters,
        'search_form': forms.SearchForm(),
    }
    return render(request, template, context)


@has_journal
@decorators.frontend_enabled
def issues(request):
    """ Renders the list of issues in the journal.

    :param request: the request associated with this call
    :return: a rendered template of all issues
    """
    issue_objects = models.Issue.objects.filter(
        journal=request.journal,
        issue_type__code='issue',
        date__lte=timezone.now(),
    )
    template = 'journal/issues.html'
    context = {
        'issues': issue_objects,
    }
    return render(request, template, context)


@has_journal
@decorators.frontend_enabled
def current_issue(request, show_sidebar=True):
    """ Renders the current journal issue"""
    issue_id = request.journal.current_issue_id
    if not issue_id:
        latest_issue = models.Issue.objects.filter(
            date=timezone.now(),
        ).order_by("-date").values("id").first()
        if latest_issue:
            issue_id = latest_issue.id
    if not issue_id:
        return redirect(reverse('journal_issues'))
    return issue(request, request.journal.current_issue_id, show_sidebar=show_sidebar)


@has_journal
@decorators.frontend_enabled
def issue(request, issue_id, show_sidebar=True):
    """ Renders a specific issue/collection in the journal.

    It also returns all the other issues/collections in the journal
    for building a navigation menu
    :param request: the request associated with this call
    :param issue_id: the ID of the issue to render
    :param show_sidebar: whether or not to show the sidebar of issues
    :return: a rendered template of this issue
    """
    issue_object = get_object_or_404(
        models.Issue.objects.prefetch_related('editors'),
        pk=issue_id,
        journal=request.journal,
        date__lte=timezone.now(),
    )

    page = request.GET.get("page", 1)
    paginator = Paginator(issue_object.get_sorted_articles(), 50)

    try:
        articles = paginator.page(page)
    except PageNotAnInteger:
        articles = paginator.page(1)
    except EmptyPage:
        articles = paginator.page(paginator.num_pages)

    issue_objects = models.Issue.objects.filter(
        journal=request.journal,
        issue_type=issue_object.issue_type,
        date__lte=timezone.now(),
    )

    editors = models.IssueEditor.objects.filter(
        issue=issue_object,
    )

    template = 'journal/issue.html'
    context = {
        'issue': issue_object,
        'issues': issue_objects,
        'structure': issue_object.structure,  # for backwards compatibility
        'articles': articles,
        'editors': editors,
        'show_sidebar': show_sidebar,
    }

    return render(request, template, context)


@has_journal
@decorators.frontend_enabled
def collections(request, issue_type_code="collection"):
    """
    Displays a list of collection Issues.
    :param request: request object
    :return: a rendered template of the collections
    """
    issue_type = get_object_or_404(
        models.IssueType,
        journal=request.journal,
        code=issue_type_code,
    )
    collections = models.Issue.objects.filter(
        journal=request.journal,
        issue_type=issue_type,
        date__lte=timezone.now(),
    ).exclude(
        # This has to be an .exclude because.filter won't do an INNER join
        articles__isnull=True,
    )

    template = 'journal/collections.html'
    context = {
        'collections': collections,
        'issue_type': issue_type,
    }

    return render(request, template, context)


@has_journal
@decorators.frontend_enabled
def collection(request, collection_id, show_sidebar=True):
    """
    A proxy view for an issue of type `Collection`.
    :param request: request object
    :param collection_id: primary key of an Issue object
    :param show_sidebar: boolean
    :return: a rendered template
    """

    return issue(request, collection_id, show_sidebar)


@decorators.frontend_enabled
@article_exists
@article_stage_accepted_or_later_required
def article(request, identifier_type, identifier):
    """ Renders an article.

    :param request: the request associated with this call
    :param identifier_type: the identifier type
    :param identifier: the identifier
    :return: a rendered template of the article
    """
    article_object = submission_models.Article.get_article(request.journal, identifier_type, identifier)

    content = None
    galleys = article_object.galley_set.all()

    # check if there is a galley file attached that needs rendering
    if article_object.is_published:
        content = get_galley_content(article_object, galleys, recover=True)
    else:
        article_object.abstract = "<p><strong>This is an accepted article with a DOI pre-assigned " \
                                  "that is not yet published.</strong></p>" + article_object.abstract

    if not article_object.large_image_file or article_object.large_image_file.uuid_filename == '':
        article_object.large_image_file = core_models.File()
        # assign the default image with a hacky patch
        # TODO: this should be set to a journal-wide setting
        article_object.large_image_file.uuid_filename = "carousel1.png"
        article_object.large_image_file.is_remote = True

    if article_object.is_published:
        store_article_access(request, article_object, 'view')

    template = 'journal/article.html'
    context = {
        'article': article_object,
        'galleys': galleys,
        'identifier_type': identifier_type,
        'identifier': identifier,
        'article_content': content,
    }

    return render(request, template, context)


@decorators.frontend_enabled
@article_exists
@article_stage_accepted_or_later_required
def print_article(request, identifier_type, identifier):
    """ Renders an article.

    :param request: the request associated with this call
    :param identifier_type: the identifier type
    :param identifier: the identifier
    :return: a rendered template of the article
    """
    article_object = submission_models.Article.get_article(request.journal, identifier_type, identifier)

    content = None
    galleys = article_object.galley_set.all()

    # check if there is a galley file attached that needs rendering
    if article_object.stage == submission_models.STAGE_PUBLISHED:
        content = get_galley_content(article_object, galleys)
    else:
        article_object.abstract = "This is an accepted article with a DOI pre-assigned that is not yet published."

    if not article_object.large_image_file or article_object.large_image_file.uuid_filename == '':
        article_object.large_image_file = core_models.File()
        # assign the default image with a hacky patch
        # TODO: this should be set to a journal-wide setting
        article_object.large_image_file.uuid_filename = "carousel1.png"
        article_object.large_image_file.is_remote = True

    store_article_access(request, article_object, 'view')

    template = 'journal/print.html'
    context = {
        'article': article_object,
        'galleys': galleys,
        'identifier_type': identifier_type,
        'identifier': identifier,
        'article_content': content
    }

    return render(request, template, context)


@has_journal
@decorators.frontend_enabled
@keyword_page_enabled
def keywords(request):
    """
    Renders a list of keywords
    :param request: HttpRequest object
    :return: a rendered template
    """
    keywords = request.journal.article_keywords()

    template = 'journal/keywords.html'
    context = {
        'keywords': keywords,
    }

    return render(request, template, context)


@has_journal
@decorators.frontend_enabled
@keyword_page_enabled
def keyword(request, keyword_id):
    """
    Displays a list of articles that use a given keyword.
    :param request: HttpRequest object
    :param keyword_id: Keyword object PK
    :return: a rendered template
    """
    keyword = get_object_or_404(submission_models.Keyword, pk=keyword_id)
    articles =  request.journal.published_articles.filter(
        keywords__pk=keyword.pk,
    )

    template = 'journal/keyword.html'
    context = {
        'keyword': keyword,
        'articles': articles,
    }

    return render(request, template, context)


@staff_member_required
@has_journal
@article_exists
def edit_article(request, identifier_type, identifier):
    """ Renders the page to edit an article. Note that security enforcement on this view is handled in the submission
    views. All this function does is to redirect to the 'submit_info' view with any identifiers translated to a PK.

    :param request: the request associated with this call
    :param identifier_type: the identifier type
    :param identifier: the identifier
    :return: a rendered template to edit the article
    """
    article_object = submission_models.Article.get_article(request.journal, identifier_type, identifier)

    return redirect(reverse('submit_info', kwargs={'article_id': article_object.pk}))


def download_galley(request, article_id, galley_id):
    """ Serves a galley file for an article

    :param request: an HttpRequest object
    :param article_id: an Article object PK
    :param galley_id: an Galley object PK
    :return: a streaming response of the requested file or a 404.
    """
    article = get_object_or_404(submission_models.Article.allarticles,
                                pk=article_id,
                                journal=request.journal,
                                date_published__lte=timezone.now(),
                                stage__in=submission_models.PUBLISHED_STAGES)
    galley = get_object_or_404(core_models.Galley, pk=galley_id)

    embed = request.GET.get('embed', False)

    if not embed == 'True':
        store_article_access(
            request,
            article,
            'download',
            galley_type=galley.type,
        )
    return files.serve_file(request, galley.file, article, public=True)


def view_galley(request, article_id, galley_id):
    """
    Serves a PDF article to the browser.

    :param request: HttpRequest object
    :param article_id: an Article object PK
    :param galley_id: a Galley object PK
    :return: an HttpResponse with a PDF attachment
    """
    article_to_serve = get_object_or_404(
        submission_models.Article.allarticles,
        pk=article_id,
        journal=request.journal,
        date_published__lte=timezone.now(),
        stage__in=submission_models.PUBLISHED_STAGES
    )
    galley = get_object_or_404(
        core_models.Galley,
        pk=galley_id,
        article=article_to_serve,
        file__mime_type='application/pdf'
    )

    store_article_access(
        request,
        article_to_serve,
        'view',
        galley_type=galley.type
    )

    return files.serve_pdf_galley_to_browser(
        request,
        galley.file,
        article_to_serve
    )


@has_request
@article_stage_accepted_or_later_or_staff_required
@file_user_required
def serve_article_file(request, identifier_type, identifier, file_id):
    """ Serves an article file.

    :param request: the request associated with this call
    :param identifier_type: the identifier type for the article
    :param identifier: the identifier for the article
    :param file_id: the file ID to serve
    :return: a streaming response of the requested file or 404
    """

    if not request.journal and request.site_type.code == 'press':
        article_object = submission_models.Article.get_press_article(
            request.press,
            identifier_type,
            identifier,
        )
    else:
        article_object = submission_models.Article.get_article(
            request.journal,
            identifier_type,
            identifier,
        )

    try:
        if file_id != "None":
            file_object = get_object_or_404(core_models.File, pk=file_id)
            return files.serve_file(request, file_object, article_object)
        else:
            raise Http404
    except Http404:
        if file_id != "None":
            raise Http404

        # if we are here then the carousel is requesting an image for an article that doesn't exist
        # return a default image instead

        return redirect(static('common/img/default_carousel/carousel1.png'))


@login_required
@article_exists
@file_edit_user_required
def replace_article_file(request, identifier_type, identifier, file_id):
    """ Renders the page to replace an article file

    :param request: the request associated with this call
    :param identifier_type: the identifier type for the article
    :param identifier: the identifier for the article
    :param file_id: the file ID to replace
    :return: a rendered template to replace the file
    """
    article_to_replace = submission_models.Article.get_article(request.journal, identifier_type, identifier)
    file_to_replace = get_object_or_404(core_models.File, pk=file_id)

    error = None

    if request.GET.get('delete', False):
        file_delete(request, article_to_replace.pk, file_to_replace.pk)
        return redirect(reverse('submit_files', kwargs={'article_id': article_to_replace.id}))

    if request.POST:

        if 'replacement' in request.POST and request.FILES:
            uploaded_file = request.FILES.get('replacement-file')
            files.overwrite_file(
                    uploaded_file,
                    file_to_replace,
                    ('articles', article_to_replace.pk),
            )
        elif not request.FILES and 'back' not in request.POST:
            messages.add_message(
                request,
                messages.WARNING,
                'No file uploaded',
            )

            url = '{url}?return={get}'.format(
                url=reverse('article_file_replace',
                            kwargs={'identifier_type': 'id',
                                    'identifier': article_to_replace.pk,
                                    'file_id': file_to_replace.pk}
                            ),
                get=request.GET.get('return', ''),
            )

            return redirect(url)

        return redirect(request.GET.get('return', reverse('core_dashboard')))

    template = "journal/replace_file.html"
    context = {
        'article': article_to_replace,
        'old_file': file_to_replace,
        'error': error,
    }

    return render(request, template, context)


@login_required
@article_exists
@file_edit_user_required
def file_reinstate(request, article_id, file_id, file_history_id):
    """ Replaces a file with an older version of itself

    :param request: the request associated with this call
    :param article_id: the article on which to replace the file
    :param file_id: the file ID to replace
    :param file_history_id: the file history object to reinstate
    :return: a redirect to the contents of the GET parameter 'return'
    """
    current_file = get_object_or_404(core_models.File, pk=file_id)
    file_history = get_object_or_404(core_models.FileHistory, pk=file_history_id)

    files.reinstate_historic_file(article, current_file, file_history)

    return redirect(request.GET['return'])


@login_required
@file_edit_user_required
def submit_files_info(request, article_id, file_id):
    """ Renders a template to submit information about a file.

    :param request: the request associated with this call
    :param article_id: the ID of the associated article
    :param file_id: the file ID for which to submit information
    :return: a rendered template to submit file information
    """
    article_object = get_object_or_404(submission_models.Article.allarticlesd, pk=article_id)
    file_object = get_object_or_404(core_models.File, pk=file_id)

    form = review_forms.ReplacementFileDetails(instance=file_object)

    if request.POST:
        form = review_forms.ReplacementFileDetails(request.POST, instance=file_object)
        if form.is_valid():
            form.save()
            # TODO: this needs a better redirect
            return redirect(reverse('kanban'))

    template = "review/submit_replacement_files_info.html"
    context = {
        'article': article_object,
        'file': file_object,
        'form': form,
    }

    return render(request, template, context)


@login_required
@file_history_user_required
def file_history(request, article_id, file_id):
    """ Renders a template to show the history of a file.

    :param request: the request associated with this call
    :param article_id: the ID of the associated article
    :param file_id: the file ID for which to view the history
    :return: a rendered template showing the file history
    """

    if request.POST:
        return redirect(request.GET['return'])

    article_object = get_object_or_404(submission_models.Article.allarticles, pk=article_id)
    file_object = get_object_or_404(core_models.File, pk=file_id)

    template = "journal/file_history.html"
    context = {
        'article': article_object,
        'file': file_object,
    }

    return render(request, template, context)


@editor_user_required
def issue_file_history(request, issue_id):
    """ Returns the file history of a given Issue Galley file

    """
    # TODO: Combine with `file_history` above, disabled until GH #865
    raise Http404
    issue_galley = get_object_or_404(models.IssueGalley, issue__pk=issue_id)
    file_object = issue_galley.file

    template = "journal/file_history.html"
    context = {
        'article': None,
        'file': file_object,
    }

    return render(request, template, context)


@login_required
@file_edit_user_required
def file_delete(request, article_id, file_id):
    """ Renders a template to delete a file.

    :param request: the request associated with this call
    :param article_id: the ID of the associated articled
    :param file_id: the file ID for which to view the history
    :return: a redirect to the URL at the GET parameter 'return'
    """
    article_object = get_object_or_404(submission_models.Article.allarticles, pk=article_id)
    file_object = get_object_or_404(core_models.File, pk=file_id)

    file_object.delete()

    return redirect(request.GET['return'])


@file_user_required
@production_user_or_editor_required
def article_file_make_galley(request, article_id, file_id):
    """ Copies a file to be a publicly available galley

    :param request: the request associated with this call
    :param article_id: the ID of the associated articled
    :param file_id: the file ID for which to view the history
    :return: a redirect to the URL at the GET parameter 'return'
    """
    article_object = get_object_or_404(submission_models.Article.allarticles, pk=article_id)
    file_object = get_object_or_404(core_models.File, pk=file_id)

    logic.create_galley_from_file(file_object, article_object, owner=request.user)

    return redirect(request.GET['return'])


def identifier_figure(request, identifier_type, identifier, file_name):
    """
    Returns a galley figure from identifier.
    :param request: HttpRequest object
    :param identifier_type: Identifier type string
    :param identifier: An Identifier
    :param file_name: a File object name
    :return: a streaming file reponse
    """
    figure_article = submission_models.Article.get_article(
        request.journal,
        identifier_type,
        identifier
    )

    if not figure_article:
        raise Http404

    article_galleys = figure_article.galley_set.all()

    galley = logic.get_best_galley(figure_article, article_galleys)

    if not galley:
        raise Http404

    figure = get_object_or_404(galley.images, original_filename=file_name)

    return files.serve_file(request, figure, figure_article)


def article_figure(request, article_id, galley_id, file_name):
    """ Returns a galley article figure

    :param request: an HttpRequest object
    :param article_id: an Article object PK
    :param galley_id: an Galley object PK
    :param file_name: an File object name
    :return: a streaming file response or a 404 if not found
    """
    figure_article = get_object_or_404(submission_models.Article, pk=article_id)
    galley = get_object_or_404(core_models.Galley, pk=galley_id, article=figure_article)
    figure = get_object_or_404(galley.images, original_filename=file_name)

    return files.serve_file(request, figure, figure_article)


@editor_user_required
def publish(request):
    """
    Displays a list of articles in pre publication for the current journal
    :param request: django request object
    :return: contextualised django object
    """
    articles = submission_models.Article.objects.filter(
        stage=submission_models.STAGE_READY_FOR_PUBLICATION,
        journal=request.journal,
    )

    template = 'journal/publish.html'
    context = {
        'articles': articles,
    }

    return render(request, template, context)


@editor_user_required
def publish_article(request, article_id):
    """
    View allows user to set an article for publication
    :param request: request object
    :param article_id: Article PK
    :return: contextualised django template
    """
    article = get_object_or_404(
        submission_models.Article,
        Q(stage=submission_models.STAGE_READY_FOR_PUBLICATION) |
        Q(stage=submission_models.STAGE_PUBLISHED),
        pk=article_id,
        journal=request.journal,
    )
    models.FixedPubCheckItems.objects.get_or_create(article=article)

    doi_data, doi = logic.get_doi_data(article)
    issues = request.journal.issues()
    new_issue_form = issue_forms.NewIssue(journal=article.journal)
    modal = request.GET.get('m', None)
    pubdate_errors = []

    if request.POST:
        if 'assign_issue' in request.POST:
            try:
                logic.handle_assign_issue(request, article, issues)
            except IntegrityError as integrity_error:
                if not article.section:
                    messages.add_message(
                        request,
                        messages.ERROR,
                        'Your article must have a section assigned.',
                    )
                else:
                    raise integrity_error

            return redirect(
                '{0}?m=issue'.format(
                    reverse(
                        'publish_article',
                        kwargs={'article_id': article.pk},
                    )
                )
            )

        if 'unassign_issue' in request.POST:
            logic.handle_unassign_issue(request, article, issues)
            return redirect(
                '{0}?m=issue'.format(
                    reverse(
                        'publish_article',
                        kwargs={'article_id': article.pk},
                    )
                )
            )

        if 'new_issue' in request.POST:
            new_issue_form, modal, new_issue = logic.handle_new_issue(request)
            if new_issue:
                return redirect(
                    '{0}?m=issue'.format(
                        reverse(
                            'publish_article',
                             kwargs={'article_id': article.pk},
                        )
                    )
                )

        if 'pubdate' in request.POST:
            date_set, pubdate_errors = logic.handle_set_pubdate(
                request,
                article,
            )
            if not pubdate_errors:
                return redirect(
                    reverse(
                        'publish_article',
                        kwargs={'article_id': article.pk},
                    )
                )
            else:
                modal = 'pubdate'

        if 'author' in request.POST:
            logic.notify_author(request, article)
            return redirect(
                reverse(
                    'publish_article',
                    kwargs={'article_id': article.pk},
                )
            )

        if 'galley' in request.POST:
            logic.set_render_galley(request, article)
            return redirect(
                reverse(
                    'publish_article',
                    kwargs={'article_id': article.pk},
                )
            )

        if 'image' in request.POST or 'delete_image' in request.POST:
            logic.set_article_image(request, article)
            shared.clear_cache()
            return redirect(
                "{0}{1}".format(
                    reverse(
                        'publish_article',
                        kwargs={'article_id': article.pk},
                    ),
                    "?m=article_image",
                )
            )

        if 'publish' in request.POST:
            article.stage = submission_models.STAGE_PUBLISHED
            article.snapshot_authors(force_update=False)
            article.close_core_workflow_objects()

            if not article.date_published:
                article.date_published = timezone.now()

            article.save()

            # Fire publication event
            kwargs = {'article': article,
                      'request': request}
            event_logic.Events.raise_event(
                event_logic.Events.ON_ARTICLE_PUBLISHED,
                task_object=article,
                **kwargs,
            )

            # Attempt to register xref DOI
            for identifier in article.identifier_set.all():
                if identifier.id_type == 'doi':
                    status, error = identifier.register()
                    messages.add_message(
                        request,
                        messages.INFO if not error else messages.ERROR,
                        status
                    )

            messages.add_message(
                request,
                messages.SUCCESS,
                'Article set for publication.',
            )

            # clear the cache
            shared.clear_cache()

            if request.journal.element_in_workflow(
                element_name='prepublication',
            ):
                workflow_kwargs = {'handshake_url': 'publish',
                                   'request': request,
                                   'article': article,
                                   'switch_stage': True}
                return event_logic.Events.raise_event(
                    event_logic.Events.ON_WORKFLOW_ELEMENT_COMPLETE,
                    task_object=article,
                    **workflow_kwargs,
                )

        return redirect(
            reverse(
                'publish_article',
                kwargs={'article_id': article.pk},
            )
        )

    template = 'journal/publish_article.html'
    context = {
        'article': article,
        'doi_data': doi_data,
        'doi': doi,
        'issues': issues,
        'new_issue_form': new_issue_form,
        'modal': modal,
        'pubdate_errors': pubdate_errors,
        'notify_author_text': logic.get_notify_author_text(request, article)
    }

    return render(request, template, context)


@require_POST
@editor_user_required
def publish_article_check(request, article_id):
    """
    A POST only view that updates checklist items on the prepublication page.
    :param request: HttpRequest object
    :param article_id: Artcle object PK
    :return: HttpResponse object
    """
    article = get_object_or_404(submission_models.Article,
                                Q(stage=submission_models.STAGE_READY_FOR_PUBLICATION) |
                                Q(stage=submission_models.STAGE_PUBLISHED),
                                pk=article_id)

    task_type = request.POST.get('task_type')
    id = request.POST.get('id')
    value = True if int(request.POST.get('value')) == 1 else False

    if not task_type or not id:
        return HttpResponse(json.dumps({'error': 'no data supplied'}), content_type="application/json")

    if task_type == 'fixed':
        update_dict = {id: value}
        for k, v in update_dict.items():
            setattr(article.fixedpubcheckitems, k, v)
        article.fixedpubcheckitems.save()

        return HttpResponse(json.dumps({'action': 'ok', 'id': value}), content_type="application/json")

    else:
        item_to_update = get_object_or_404(models.PrePublicationChecklistItem, pk=id, article=article)
        item_to_update.completed = True if int(request.POST.get('value')) == 1 else False
        item_to_update.completed_by = request.user
        item_to_update.completed_on = timezone.now()
        item_to_update.save()
        return HttpResponse(json.dumps({'action': 'ok', 'id': value}), content_type="application/json")


@editor_user_required
def manage_issues(request, issue_id=None, event=None):
    """
    Displays a list of Issue objects, allows them to be sorted and viewed.
    :param request: HttpRequest object
    :param issue_id: Issue object PJ
    :param event: string, 'issue', 'delete' or 'remove'
    :return: HttpResponse object or HttpRedirect if POSTed
    """
    from core.logic import resize_and_crop
    issue_list = models.Issue.objects.filter(journal=request.journal)
    issue, modal, form, galley_form = None, None, issue_forms.NewIssue(journal=request.journal), None

    if issue_id:
        issue = get_object_or_404(models.Issue, pk=issue_id)
        form = issue_forms.NewIssue(instance=issue, journal=issue.journal)
        galley_form = issue_forms.IssueGalleyForm()
        if event == 'edit':
            modal = 'issue'
        if event == 'delete':
            modal = 'deleteme'
        if event == 'remove':
            article_id = request.GET.get('article')
            article = get_object_or_404(submission_models.Article, pk=article_id, pk__in=issue.article_pks)
            issue.articles.remove(article)
            return redirect(reverse('manage_issues_id', kwargs={'issue_id': issue.pk}))

    if request.POST:
        if 'make_current' in request.POST:
            issue = models.Issue.objects.get(id=request.POST['make_current'])
            request.journal.current_issue = issue
            request.journal.save()
            issue = None
            return redirect(reverse('manage_issues'))

        if 'delete_issue' in request.POST:
            issue.delete()
            return redirect(reverse('manage_issues'))

        if 'sort' in request.POST:
            logic.sort_issues(request, issue_list)
            return redirect(reverse('manage_issues'))

        if issue:
            form = issue_forms.NewIssue(request.POST, request.FILES, instance=issue, journal=request.journal)
        else:
            form = issue_forms.NewIssue(request.POST, request.FILES, journal=request.journal)

        if form.is_valid():
            save_issue = form.save(commit=False)
            save_issue.journal = request.journal
            save_issue.save()
            if request.FILES and save_issue.large_image:
                resize_and_crop(save_issue.large_image.path, [750, 324])
            if issue:
                return redirect(reverse('manage_issues_id', kwargs={'issue_id': issue.pk}))
            else:
                return redirect(reverse('manage_issues'))
        else:
            modal = 'issue'

    template = 'journal/manage/issues.html'
    context = {
        'issues': issue_list if not issue else [issue],
        'issue': issue,
        'form': form,
        'modal': modal,
        'galley_form': galley_form,
        'articles': issue.get_sorted_articles(published_only=False) if issue else None,
    }

    return render(request, template, context)


@has_journal
@editor_user_required
def manage_issue_display(request):
    """
    Allows an Editor to change the way issue titles are displayed.
    :param request: HttpRequest
    :return: HttpResponse or HttpRedirect
    """
    issue_display_form = forms.IssueDisplayForm(instance=request.journal)

    if request.POST:
        issue_display_form = forms.IssueDisplayForm(
            request.POST,
            instance=request.journal,
        )

        if issue_display_form.is_valid():
            issue_display_form.save()
            return redirect(
                reverse(
                    'manage_issue_display',
                )
            )

    template = 'journal/manage/issue_display.html'
    context = {
        'issue_display_form': issue_display_form,
    }

    return render(request, template, context)


@editor_user_required
def issue_galley(request, issue_id, delete=False):
    issue = get_object_or_404(models.Issue, pk=issue_id)

    if request.method == 'POST':
        form = issue_forms.IssueGalleyForm(request.POST, request.FILES)
        if 'delete' in request.POST:
            issue_galley = get_object_or_404(models.IssueGalley, issue=issue)
            issue_galley.delete()
            messages.info(request, "Issue Galley Deleted")
        elif form.is_valid():
            uploaded_file = request.FILES["file"]
            try:
                issue_galley = models.IssueGalley.objects.get(issue=issue)
                issue_galley.replace_file(uploaded_file)
            except models.IssueGalley.DoesNotExist:
                file_obj = files.save_file(
                    request,
                    uploaded_file,
                    label=issue.issue_title,
                    public=False,
                    path_parts=(models.IssueGalley.FILES_PATH, issue.pk),
                )
                models.IssueGalley.objects.create(
                    file=file_obj,
                    issue=issue,
                )

            messages.info(request, "Issue Galley Uploaded")
        elif form.errors:
            messages.error(
                    request,
                    "\n".join(field.errors.as_text() for field in form)
         )

    return redirect(reverse('manage_issues_id', kwargs={'issue_id': issue.pk}))


@editor_user_required
def sort_issue_sections(request, issue_id):
    issue = get_object_or_404(models.Issue, pk=issue_id, journal=request.journal)
    sections = issue.all_sections

    if request.POST:
        if 'up' in request.POST:
            section_id = request.POST.get('up')
            section_to_move_up = get_object_or_404(submission_models.Section, pk=section_id, journal=request.journal)

            if section_to_move_up != issue.first_section:
                section_to_move_up_index = sections.index(section_to_move_up)
                section_to_move_down = sections[section_to_move_up_index - 1]

                section_to_move_up_ordering, c = models.SectionOrdering.objects.get_or_create(
                    issue=issue,
                    section=section_to_move_up)
                section_to_move_down_ordering, c = models.SectionOrdering.objects.get_or_create(
                    issue=issue,
                    section=section_to_move_down)

                section_to_move_up_ordering.order = section_to_move_up_index - 1
                section_to_move_down_ordering.order = section_to_move_up_index

                section_to_move_up_ordering.save()
                section_to_move_down_ordering.save()
            else:
                messages.add_message(request, messages.WARNING, 'You cannot move the first section up the order list')

        elif 'down' in request.POST:
            section_id = request.POST.get('down')
            section_to_move_down = get_object_or_404(submission_models.Section, pk=section_id, journal=request.journal)

            if section_to_move_down != issue.last_section:
                section_to_move_down_index = sections.index(section_to_move_down)
                section_to_move_up = sections[section_to_move_down_index + 1]

                section_to_move_up_ordering, c = models.SectionOrdering.objects.get_or_create(
                    issue=issue,
                    section=section_to_move_up)
                section_to_move_down_ordering, c = models.SectionOrdering.objects.get_or_create(
                    issue=issue,
                    section=section_to_move_down)

                section_to_move_up_ordering.order = section_to_move_down_index
                section_to_move_down_ordering.order = section_to_move_down_index + 1

                section_to_move_up_ordering.save()
                section_to_move_down_ordering.save()

            else:
                messages.add_message(request, messages.WARNING, 'You cannot move the last section down the order list')

    else:
        messages.add_message(request, messages.WARNING, 'This page accepts post requests only.')
    return redirect(reverse('manage_issues_id', kwargs={'issue_id': issue.pk}))


@editor_user_required
def issue_add_article(request, issue_id):
    """
    Allows an editor to add an article to an issue.
    :param request: django request object
    :param issue_id: PK of an Issue object
    :return: a contextualised django template
    """

    issue = get_object_or_404(models.Issue, pk=issue_id, journal=request.journal)
    articles = submission_models.Article.objects.filter(
            journal=request.journal,
    ).exclude(
        Q(pk__in=issue.article_pks) | Q(stage=submission_models.STAGE_REJECTED)
    )

    if request.POST.get('article'):
        article_id = request.POST.get('article')
        article = get_object_or_404(submission_models.Article, pk=article_id, journal=request.journal)

        if not article.section:
            messages.add_message(request, messages.WARNING, 'Articles without a section cannot be added to an issue.')
            return redirect(reverse('issue_add_article', kwargs={'issue_id': issue.pk}))
        else:
            issue.articles.add(article)
        return redirect(reverse('manage_issues_id', kwargs={'issue_id': issue.pk}))

    template = 'journal/manage/issue_add_article.html'
    context = {
        'issue': issue,
        'articles': articles,
    }

    return render(request, template, context)


@editor_user_required
def add_guest_editor(request, issue_id):
    """
    Allows an editor to add a guest editor to an issue.
    :param request: django request object
    :param issue_id: PK of an Issue object
    :return: a contextualised django template
    """
    issue = get_object_or_404(
        models.Issue,
        pk=issue_id,
        journal=request.journal,
    )

    current_editors = issue.editors.all()
    users = logic.potential_issue_editors(request.journal, current_editors)

    if request.POST:
        if 'user' in request.POST:
            user_id = request.POST.get('user')
            role = request.POST.get('role')

            user = get_object_or_404(core_models.Account, pk=user_id)

            if user in current_editors:
                messages.add_message(
                    request,
                    messages.WARNING,
                    'User is already a guest editor.',
                )
            elif user not in users:
                messages.add_message(
                    request,
                    messages.WARNING,
                    'This user is not a member of this journal.',
                )
            else:
                models.IssueEditor.objects.create(
                    issue=issue,
                    account=user,
                    role=role,
                )

            return redirect(
                reverse(
                    'manage_add_guest_editor',
                    kwargs={'issue_id': issue.pk}
                )
            )

    template = 'journal/manage/add_guest_editor.html'
    context = {
        'issue': issue,
        'users': users,
        'editors': models.IssueEditor.objects.filter(issue=issue),
    }

    return render(request, template, context)


@editor_user_required
@require_POST
def remove_issue_editor(request, issue_id):
    issue = get_object_or_404(
        models.Issue,
        pk=issue_id,
        journal=request.journal,
    )

    if 'user_remove' in request.POST:
        issue_editor_id = request.POST.get('user_remove', 0)

        if issue_editor_id:
            try:
                models.IssueEditor.objects.get(
                    pk=issue_editor_id,
                ).delete()
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    'Editor removed from Issue.',
                )
            except models.IssueEditor.DoesNotExist:
                messages.add_message(
                    request,
                    messages.WARNING,
                    'Issue Editor not found.',
                )
        else:
            messages.add_message(
                request,
                messages.WARNING,
                'No Issue Editor ID supplied.',
            )

    return redirect(
        reverse(
            'manage_add_guest_editor',
            kwargs={'issue_id': issue.pk},
        )
    )


@csrf_exempt
@editor_user_required
def issue_order(request):
    """
    Takes a list of issue ids and updates their ordering.
    :param request: django request object
    :return: a message
    """

    issues = models.Issue.objects.filter(journal=request.journal)

    if request.POST:
        ids = [int(_id) for _id in request.POST.getlist('issues[]')]

        for issue in issues:
            order = ids.index(issue.pk)
            issue.order = order
            issue.save()

    return HttpResponse('Thanks')


@csrf_exempt
@editor_user_required
def issue_article_order(request, issue_id=None):
    """
    Takes a list if IDs and re-orders an issue's articles.
    :param request: django request object
    :param issue_id: PK of an Issue object
    :return: An ok or error message.
    """

    issue = get_object_or_404(models.Issue, pk=issue_id, journal=request.journal)
    if request.POST:
        ids = request.POST.getlist('articles[]')
        ids = [int(_id) for _id in ids]
        articles = submission_models.Article.objects.filter(
            id__in=ids, journal=request.journal)
        section = None

        for order, article in enumerate(sorted(
            articles, key=lambda x: ids.index(x.pk)
        )):
            section = article.section
            if not issue.articles.filter(id=article.id).exists():
                logger.error(
                    "Attempted to set order for article %d within issue %s"
                    "" % (article.pk, issue)
                )
                continue
            elif section is not None and section != article.section:
                logger.error(
                    "Attempted to order articles from mixed sections"
                    " %s" % ids
                )
                continue
            models.ArticleOrdering.objects.update_or_create(
                issue=issue,
                article=article,
                defaults={
                    'order': order,
                    'section': article.section,
                }
            )

    return JsonResponse({'status': 'okay'})


@editor_user_required
def manage_archive(request):
    """
    Allows the editor to view information about an article that has been published already.
    :param request: request object
    :return: contextualised django template
    """
    published_articles = submission_models.Article.objects.filter(
        journal=request.journal,
        stage=submission_models.STAGE_PUBLISHED
    ).order_by(
        '-date_published'
    )
    rejected_articles = submission_models.Article.objects.filter(
        journal=request.journal,
        stage=submission_models.STAGE_REJECTED
    ).order_by(
        '-date_declined'
    )

    template = 'journal/manage/archive.html'
    context = {
        'published_articles': published_articles,
        'rejected_articles': rejected_articles,
    }

    return render(request, template, context)


@editor_user_required
def manage_archive_article(request, article_id):
    """
    Allows an editor to edit a previously published article.
    :param request: HttpRequest object
    :param article_id: Article object PK
    :return: HttpResponse or HttpRedirect if Posted
    """
    from production import logic as production_logic
    from identifiers import models as identifier_models
    from submission import forms as submission_forms

    article = get_object_or_404(submission_models.Article, pk=article_id)
    galleys = production_logic.get_all_galleys(article)
    identifiers = identifier_models.Identifier.objects.filter(article=article)

    if request.POST:

        if 'file' in request.FILES:
            label = request.POST.get('label')
            for uploaded_file in request.FILES.getlist('file'):
                try:
                    production_logic.save_galley(
                        article,
                        request,
                        uploaded_file,
                        True,
                        label=label,
                    )
                except UnicodeDecodeError:
                    messages.add_message(
                        request,
                        messages.ERROR,
                        "Uploaded file is not UTF-8 encoded",
                    )
                except production_logic.ZippedGalleyError:
                    messages.add_message(request, messages.ERROR,
                        "Galleys must be uploaded individually, not zipped",
                    )

        if 'delete_note' in request.POST:
            note_id = int(request.POST['delete_note'])
            publisher_note = submission_models.PublisherNote.objects.get(pk=note_id)
            publisher_note.delete()

        if 'add_publisher_note' in request.POST:
            pn = submission_models.PublisherNote()
            pn.creator = request.user
            pn.sequence = 0
            pn_form = submission_forms.PublisherNoteForm(data=request.POST, instance=pn)
            pn_form.save()

            article.publisher_notes.add(pn)
            article.save()

        if 'save_publisher_note' in request.POST:
            note_id = int(request.POST['save_publisher_note'])
            pn = submission_models.PublisherNote.objects.get(pk=note_id)
            pn_form = submission_forms.PublisherNoteForm(data=request.POST, instance=pn)
            pn_form.save()

        return redirect(reverse('manage_archive_article', kwargs={'article_id': article.pk}))

    newnote_form = submission_forms.PublisherNoteForm()

    note_forms = []

    for publisher_note in article.publisher_notes.all():
        note_form = submission_forms.PublisherNoteForm(instance=publisher_note)
        note_forms.append(note_form)

    template = 'journal/manage/archive_article.html'
    context = {
        'article': article,
        'galleys': galleys,
        'identifiers': identifiers,
        'newnote_form': newnote_form,
        'note_forms': note_forms
    }

    return render(request, template, context)


@editor_user_required
def publication_schedule(request):
    """
    Displays a list of articles that have been set for publication but are not yet published.
    :param request: HttpRequest object
    :return: HttpReponse
    """
    article_list = submission_models.Article.objects.filter(journal=request.journal,
                                                            date_published__gte=timezone.now())

    template = 'journal/manage/publication_schedule.html'
    context = {
        'articles': article_list,
    }

    return render(request, template, context)


@login_required
@decorators.frontend_enabled
def become_reviewer(request):
    """
    If a user is signed in and not a reviewer, lets them become one, otherwsie asks them to login/tells them they
    are already a reviewer
    :param request: django request object
    :return: a contextualised django template
    """

    # The user needs to login before we can do anything else
    code = 'not-logged-in'
    message = _('You must login before you can become a reviewer. Click the button below to login.')

    if request.user and request.user.is_authenticated() and not request.user.is_reviewer(request):
        # We have a user, they are logged in and not yet a reviewer
        code = 'not-reviewer'
        message = _('You are not yet a reviewer for this journal. Click the button below to become a reviewer.')

    elif request.user and request.user.is_authenticated() and request.user.is_reviewer(request):
        # The user is logged in, and is already a reviewer
        code = 'already-reviewer'
        message = _('You are already a reviewer.')

    if request.POST.get('action', None) == 'go':
        request.user.add_account_role('reviewer', request.journal)
        messages.add_message(request, messages.SUCCESS, _('You are now a reviewer'))
        return redirect(reverse('core_dashboard'))

    template = 'journal/become_reviewer.html'
    context = {
        'code': code,
        'message': message,
    }

    return render(request, template, context)


@decorators.frontend_enabled
def contact(request):
    """
    Displays a form that allows a user to contact admins or editors.
    :param request: HttpRequest object
    :return: HttpResponse or HttpRedirect if POST
    """
    subject = request.GET.get('subject', '')
    contacts = core_models.Contacts.objects.filter(content_type=request.model_content_type,
                                                   object_id=request.site_type.pk)

    contact_form = forms.ContactForm(subject=subject, contacts=contacts)

    if request.POST:
        contact_form = forms.ContactForm(request.POST, contacts=contacts)

        if contact_form.is_valid():
            new_contact = contact_form.save(commit=False)
            new_contact.client_ip = shared.get_ip_address(request)
            new_contact.content_type = request.model_content_type
            new_contact.object_ic = request.site_type.pk
            new_contact.save()

            logic.send_contact_message(new_contact, request)
            messages.add_message(request, messages.SUCCESS, 'Your message has been sent.')
            return redirect(reverse('contact'))

    template = 'journal/contact.html'
    context = {
        'contact_form': contact_form,
        'contacts': contacts,
    }

    return render(request, template, context)


@decorators.frontend_enabled
def editorial_team(request, group_id=None):
    """
    Displays a list of Editorial team members, an optional ID can be supplied to limit the display to a group only.
    :param request: HttpRequest object
    :param group_id: EditorailGroup object PK
    :return: HttpResponse object
    """
    if group_id:
        editorial_groups = core_models.EditorialGroup.objects.filter(journal=request.journal, pk=group_id)
    else:
        editorial_groups = core_models.EditorialGroup.objects.filter(journal=request.journal)

    template = 'journal/editorial_team.html'
    context = {
        'editorial_groups': editorial_groups,
        'group_id': group_id,
    }

    return render(request, template, context)


@has_journal
@decorators.frontend_enabled
def author_list(request):
    """
    Displays list of authors.
    :param request: HttpRequest object
    :return: HttpResponse object
    """
    author_list = request.journal.users_with_role('author')
    template = 'journal/authors.html'

    context = {
        'author_list': author_list,
    }
    return render(request, template, context)


def sitemap(request):
    """
    Renders an XML sitemap based on articles and pages available to the journal.
    :param request: HttpRequest object
    :return: HttpResponse object
    """
    articles = submission_models.Article.objects.filter(date_published__lte=timezone.now(), journal=request.journal)
    cms_pages = cms_models.Page.objects.filter(object_id=request.site_type.id, content_type=request.model_content_type)

    template = 'journal/sitemap.xml'

    context = {
        'articles': articles,
        'cms_pages': cms_pages,
    }
    return render(request, template, context, content_type="application/xml")


@decorators.frontend_enabled
def search(request):
    """
    Allows a user to search for articles by name or author name.
    :param request: HttpRequest object
    :return: HttpResponse object
    """
    articles = []
    search_term = None
    keyword = None
    redir = False
    sort = 'title'

    search_term, keyword, sort, form, redir = logic.handle_search_controls(request)

    if redir:
        return redir
    from itertools import chain
    if search_term:
        escaped = re.escape(search_term)
        # checks titles, keywords and subtitles first,
        # then matches author based on below regex split search term.
        split_term = [re.escape(word) for word in search_term.split(" ")]
        split_term.append(escaped)
        search_regex = "^({})$".format(
            "|".join({name for name in split_term})
        )
        articles = submission_models.Article.objects.filter(
                    (
                        Q(title__icontains=search_term) |
                        Q(keywords__word__iregex=search_regex) |
                        Q(subtitle__icontains=search_term)
                    )
                    |
                    (
                        Q(frozenauthor__first_name__iregex=search_regex) |
                        Q(frozenauthor__last_name__iregex=search_regex)
                    ),
                    journal=request.journal,
                    stage=submission_models.STAGE_PUBLISHED,
                    date_published__lte=timezone.now()
                ).distinct().order_by(sort)

    # just single keyword atm. but keyword is included in article_search.
    elif keyword:
        articles = submission_models.Article.objects.filter(
            keywords__word=keyword,
            journal=request.journal,
            stage=submission_models.STAGE_PUBLISHED,
            date_published__lte=timezone.now()
        ).order_by(sort)

    keyword_limit = 20
    popular_keywords = submission_models.Keyword.objects.filter(
            article__journal=request.journal,
            article__stage=submission_models.STAGE_PUBLISHED,
            article__date_published__lte=timezone.now(),
        ).annotate(articles_count=Count('article')).order_by("-articles_count")[:keyword_limit]

    template = 'journal/search.html'
    context = {
        'articles': articles,
        'article_search': search_term,
        'keyword': keyword,
        'form': form,
        'sort': sort,
        'all_keywords': popular_keywords
    }

    return render(request, template, context)


@has_journal
def submissions(request):
    """
    Displays a submission information page with info on sections and licenses etc.
    :param request: HttpRequest object
    :return: HttpResponse object
    """
    template = 'journal/submissions.html'

    if request.journal.disable_front_end:
        template = 'admin/journal/submissions.html'

    context = {
        'sections': submission_models.Section.objects.language().fallbacks(
            'en'
        ).filter(
            journal=request.journal,
            public_submissions=True,
        ),
        'licenses': submission_models.Licence.objects.filter(
            journal=request.journal,
            available_for_submission=True,
        )
    }

    return render(request, template, context)


@editor_user_required
def manage_article_log(request, article_id):
    """
    Displays a list of article log items.
    :param request: HttpRequest object
    :param article_id: Article object PK
    :return: HttpResponse object
    """
    article = get_object_or_404(submission_models.Article, pk=article_id)
    content_type = ContentType.objects.get_for_model(article)
    log_entries = utils_models.LogEntry.objects.filter(content_type=content_type, object_id=article.pk)

    if request.POST and settings.ENABLE_ENHANCED_MAILGUN_FEATURES:
        call_command('check_mailgun_stat', article_id=article_id)
        return redirect(reverse('manage_article_log', kwargs={'article_id': article.pk}))

    template = 'journal/article_log.html'
    context = {
        'article': article,
        'log_entries': log_entries,
        'return': request.GET.get('return', None)
    }

    return render(request, template, context)


@editor_user_required
def resend_logged_email(request, article_id, log_id):
    article = get_object_or_404(submission_models.Article, pk=article_id)
    log_entry = get_object_or_404(utils_models.LogEntry, pk=log_id)
    form = forms.ResendEmailForm(log_entry=log_entry)
    close = False

    if request.POST and 'resend' in request.POST:
        form = forms.ResendEmailForm(request.POST, log_entry=log_entry)

        if form.is_valid():
            logic.resend_email(article, log_entry, request, form)
            close = True

    template = 'journal/resend_logged_email.html'
    context = {
        'article': article,
        'log_entry': log_entry,
        'form': form,
        'close': close,
    }

    return render(request, template, context)


@has_journal
@editor_user_required
def send_user_email(request, user_id, article_id=None):
    user = get_object_or_404(core_models.Account, pk=user_id)
    form = forms.EmailForm(
        initial={'body': '<br/ >{signature}'.format(
            signature=request.user.signature)},
    )
    close = False
    article = None

    if article_id:
        article = get_object_or_404(
            submission_models.Article,
            pk=article_id
        )

    if request.POST and 'send' in request.POST:
        form = forms.EmailForm(request.POST)

        if form.is_valid():
            logic.send_email(
                user,
                form,
                request,
                article,
            )
            close = True

    template = 'admin/journal/send_user_email.html'
    context = {
        'user': user,
        'close': close,
        'form': form,
        'article': article,
    }

    return render(request, template, context)


@editor_user_required
def new_note(request, article_id):
    """
    Generates a new Note object, must be POST.
    :param request: HttpRequest object
    :param article_id: Article object PK
    :return: HttpResponse object
    """
    article = get_object_or_404(submission_models.Article, pk=article_id)

    if request.POST:

        note = request.POST.get('note')

        sav_note = submission_models.Note.objects.create(
            article=article,
            creator=request.user,
            text=note,
        )

        return_dict = {'id': sav_note.pk, 'note': sav_note.text, 'initials': sav_note.creator.initials(),
                       'date_time': str(sav_note.date_time),
                       'html': logic.create_html_snippet(sav_note)}

    else:

        return_dict = {'error': 'This request must be made with POST'}

    return HttpResponse(json.dumps(return_dict), content_type="application/json")


@editor_user_required
def delete_note(request, article_id, note_id):
    """
    Deletes a Note object.
    :param request: HttpRequest object
    :param article_id: Article object PK
    :param note_id: Note object PK
    :return: HttpResponse
    """
    note = get_object_or_404(submission_models.Note, pk=note_id)
    note.delete()

    return HttpResponse


def download_journal_file(request, file_id):
    file = get_object_or_404(core_models.File, pk=file_id)

    if file.privacy == 'public' or (request.user.is_authenticated() and request.user.is_staff) or \
            (request.user.is_authenticated() and request.user.is_editor(request)):
        return files.serve_journal_cover(request, file)
    else:
        raise Http404


def download_table(request, identifier_type, identifier, table_name):
    """
    For an JATS xml document, renders it into HTML and pulls a CSV from there.
    :param request: HttpRequest
    :param identifier_type: Article Identifier type eg. id or doi
    :param identifier: Article Identifier eg. 123 or 10.1167/1234
    :param table_name: The ID of the table inside the HTML
    :return: StreamingHTTPResponse with CSV attached
    """
    article = submission_models.Article.get_article(request.journal, identifier_type, identifier)
    galley = article.get_render_galley

    if galley.file.mime_type.endswith('/xml'):
        content = galley.file_content()
        table = logic.get_table_from_html(table_name, content)
        csv = logic.parse_html_table_to_csv(table, table_name)
        return files.serve_temp_file(csv, '{0}.csv'.format(table_name))


def download_supp_file(request, article_id, supp_file_id):
    article = get_object_or_404(submission_models.Article.allarticles, pk=article_id,
                                stage=submission_models.STAGE_PUBLISHED)
    supp_file = get_object_or_404(core_models.SupplementaryFile, pk=supp_file_id)

    return files.serve_file(request, supp_file.file, article, public=True)


@staff_member_required
def texture_edit(request, file_id):
    file = get_object_or_404(core_models.File, pk=file_id)

    template = 'admin/journal/texture.html'
    context = {
        'file': file,
        'content': files.get_file(file, file.article).replace('\n', '')
    }

    return render(request, template, context)


@editor_user_required
def document_management(request, article_id):
    document_article = get_object_or_404(submission_models.Article, pk=article_id)
    article_files = core_models.File.objects.filter(article_id=document_article.pk)
    return_url = request.GET.get('return', '/dashboard/')

    if request.POST and request.FILES:

        if 'manu' in request.POST:
            from core import files as core_files
            file = request.FILES.get('manu-file')
            new_file = core_files.save_file_to_article(file, document_article,
                                                       request.user, label='MS File', is_galley=False)
            document_article.manuscript_files.add(new_file)
            messages.add_message(request, messages.SUCCESS, 'Production file uploaded.')

        if 'prod' in request.POST:
            from production import logic as prod_logic
            file = request.FILES.get('prod-file')
            prod_logic.save_prod_file(document_article, request, file, 'Production Ready File')
            messages.add_message(request, messages.SUCCESS, 'Production file uploaded.')

        if 'proof' in request.POST:
            from production import logic as prod_logic
            file = request.FILES.get('proof-file')
            prod_logic.save_galley(document_article, request, file, True, 'File for Proofing')
            messages.add_message(request, messages.SUCCESS, 'Proofing file uploaded.')

        return redirect('{0}?return={1}'.format(reverse('document_management', kwargs={'article_id':document_article.pk}),
                                        return_url))

    template = 'admin/journal/document_management.html'
    context = {
        'files': article_files,
        'article': document_article,
        'return_url': return_url,
    }

    return render(request, template, context)


def download_issue(request, issue_id):
    issue_object = get_object_or_404(
        models.Issue,
        pk=issue_id,
        journal=request.journal,
    )
    articles = issue_object.get_sorted_articles()

    galley_files = []

    for article in articles:
        for galley in article.galley_set.all():
            store_article_access(
                request,
                article,
                'download',
                galley_type=galley.type,
            )
            galley_files.append(galley.file)

    zip_file, file_name = files.zip_article_files(
        galley_files,
        article_folders=True,
    )
    return files.serve_temp_file(zip_file, file_name)


def download_issue_galley(request, issue_id, galley_id):
    issue_galley = get_object_or_404(
            models.IssueGalley,
            pk=galley_id,
            issue__pk=issue_id,
    )

    return issue_galley.serve(request)


def doi_redirect(request, identifier_type, identifier):
    """
    Fetches an article object from a DOI and redirects to the local url.
    :param request: HttpRequest
    :param identifier_type: String, Identifier type
    :param identifier: DOI string
    :return: HttpRedirect or Http404
    """
    article_object = submission_models.Article.get_article(
        request.journal,
        identifier_type,
        identifier,
    )

    if not article_object:
        logger.debug("No article found with this DOI.")
        raise Http404()

    return redirect(article_object.local_url)


def serve_article_xml(request, identifier_type, identifier):
    article_object = submission_models.Article.get_article(
        request.journal,
        identifier_type,
        identifier,
    )

    if not article_object:
        raise Http404

    xml_galleys = article_object.galley_set.filter(
        file__mime_type__in=files.XML_MIMETYPES,
    )

    if xml_galleys.exists():

        if xml_galleys.count() > 1:
            logger.error("Found multiple XML galleys for article {id}, "
                         "returning first match".format(id=article_object.pk))

        xml_galley = xml_galleys[0]
    else:
        raise Http404

    return HttpResponse(
        xml_galley.file.get_file(article_object),
        content_type=xml_galley.file.mime_type,
    )
