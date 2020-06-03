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
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.core.cache import cache

from repository import forms, logic as repository_logic, models
from submission import models as submission_models, forms as submission_forms, logic
from core import models as core_models, files
from metrics.logic import store_article_access
from utils import shared as utils_shared
from events import logic as event_logic
from identifiers import logic as ident_logic
from security.decorators import (
    preprint_editor_or_author_required,
    is_article_preprint_editor,
    is_preprint_editor,
)


def repository_home(request):
    """
    Displays the preprints home page with search box and 6 latest preprints publications
    :param request: HttpRequest object
    :return: HttpResponse
    """
    preprints = models.Preprint.objects.filter(
        repository=request.repository,
        date_published__lte=timezone.now(),
    )
    subjects = models.Subject.objects.filter(
        repository=request.repository,
    ).prefetch_related(
        'preprint_set',
    )

    template = 'repository/home.html'
    context = {
        'preprints': preprints,
        'subjects': subjects,
    }

    return render(request, template, context)


@login_required
def repository_dashboard(request):
    """
    Displays a list of an author's preprints.
    :param request: HttpRequest object
    :return: HttpResponse
    """
    preprints = submission_models.Article.preprints.filter(Q(authors=request.user) | Q(owner=request.user),
                                                           date_submitted__isnull=False).distinct()

    incomplete_preprints = submission_models.Article.preprints.filter(Q(authors=request.user) | Q(owner=request.user),
                                                                      date_submitted__isnull=True)

    template = 'admin/preprints/dashboard.html'
    context = {
        'preprints': preprints,
        'incomplete_preprints': incomplete_preprints,
    }

    return render(request, template, context)


@preprint_editor_or_author_required
def preprints_author_article(request, article_id):
    """
    Allows authors to view the metadata and replace galley files for their articles.
    :param request: HttpRequest
    :param article_id: Article PK
    :return: HttpRedirect if POST or HttpResponse
    """
    preprint = get_object_or_404(submission_models.Article.preprints, pk=article_id)
    metrics_summary = repository_logic.metrics_summary([preprint])

    if request.POST:
        if 'submit' in request.POST:
            return repository_logic.handle_preprint_submission(request, preprint)
        else:
            repository_logic.handle_author_post(request, preprint)
            return redirect(reverse('preprints_author_article', kwargs={'article_id': preprint.pk}))

    template = 'admin/preprints/author_article.html'
    context = {
        'preprint': preprint,
        'metrics_summary': metrics_summary,
        'preprint_journals': repository_logic.get_list_of_preprint_journals(),
        'pending_updates': models.VersionQueue.objects.filter(article=preprint, date_decision__isnull=True)
    }

    return render(request, template, context)


def repository_about(request):
    """
    Displays the about page with text about preprints
    :param request: HttpRequest object
    :return: HttpResponse
    """
    template = 'repository/about.html'
    context = {

    }

    return render(request, template, context)


def repository_list(request, subject_slug=None):
    """
    Displays a list of all published preprints.
    :param request: HttpRequest
    :return: HttpResponse
    """
    if subject_slug:
        subject = get_object_or_404(models.Subject, slug=subject_slug)
        preprints = subject.preprint_set.filter(
            repository=request.repository,
            date_published__lte=timezone.now(),
        )
    else:
        subject = None
        preprints = models.Preprint.objects.filter(
            date_published__lte=timezone.now(),
            repository=request.repository,
        )

    paginator = Paginator(preprints, 15)
    page = request.GET.get('page', 1)

    try:
        preprints = paginator.page(page)
    except PageNotAnInteger:
        preprints = paginator.page(1)
    except EmptyPage:
        preprints = paginator.page(paginator.num_pages)

    template = 'repository/list.html'
    context = {
        'preprints': preprints,
        'subject': subject,
        'subjects': models.Subject.objects.filter(enabled=True)
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
             Q(keywords__word__in=split_search_term)),
            stage=submission_models.STAGE_PREPRINT_PUBLISHED, date_published__lte=timezone.now()
        )
        article_search = [article for article in article_search]

        institution_query = reduce(operator.and_, (Q(institution__icontains=x) for x in split_search_term))

        from_author = core_models.Account.objects.filter(
            (Q(first_name__in=split_search_term) |
             Q(last_name__in=split_search_term) |
             institution_query)
        )

        articles_from_author = [article for article in submission_models.Article.preprints.filter(
            authors__in=from_author,
            stage=submission_models.STAGE_PREPRINT_PUBLISHED,
            date_published__lte=timezone.now())]

        articles = set(article_search + articles_from_author)

    else:
        articles = submission_models.Article.preprints.all()

    if request.POST:
        search_term = request.POST.get('search_term')
        return redirect(reverse('preprints_search_with_term', kwargs={'search_term': search_term}))

    template = 'preprints/list.html'
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
                                stage=submission_models.STAGE_PREPRINT_PUBLISHED,
                                date_published__lte=timezone.now())
    comments = models.Comment.objects.filter(article=article, is_public=True)
    form = forms.CommentForm()

    if request.POST:

        if not request.user.is_authenticated:
            messages.add_message(request, messages.WARNING, 'You must be logged in to comment')
            return redirect(reverse('core_login'))

        form = forms.CommentForm(request.POST)

        if form.is_valid():
            comment = form.save(commit=False)
            repository_logic.handle_comment_post(request, article, comment)
            return redirect(reverse('preprints_article', kwargs={'article_id': article_id}))

    pdf = repository_logic.get_pdf(article)
    html = repository_logic.get_html(article)
    store_article_access(request, article, 'view')

    template = 'preprints/article.html'
    context = {
        'article': article,
        'galleys': article.galley_set.all(),
        'pdf': pdf,
        'html': html,
        'comments': comments,
        'form': form,
    }

    return render(request, template, context)


def preprints_pdf(request, article_id):

    pdf_url = request.GET.get('file')

    template = 'preprints/pdf.html'
    context = {
        'pdf_url': pdf_url,
    }
    return render(request, template, context)


def preprints_editors(request):
    """
    Displays lists of preprint editors by their subject group.
    :param request: HttpRequest
    :return: HttpResponse
    """
    subjects = models.Subject.objects.filter(enabled=True)

    template = 'preprints/editors.html'
    context = {
        'subjects': subjects,
    }

    return render(request, template, context)


@login_required
def repository_submit(request, preprint_id=None):
    """
    Handles initial steps of generating a preprints submission.
    :param request: HttpRequest
    :return: HttpResponse or HttpRedirect
    """
    article = repository_logic.get_preprint_article_if_id(request, preprint_id)

    # TODO: FIX THIS
    additional_fields = submission_models.Field.objects.filter(
        press=request.press,
    )
    form = forms.PreprintInfo(
        instance=article,
        additional_fields=additional_fields,
        request=request,
    )

    if request.POST:
        form = forms.PreprintInfo(
            request.POST,
            instance=article,
            additional_fields=additional_fields,
            request=request,
        )

        if form.is_valid():
            article = form.save()
            return redirect(
                reverse(
                    'preprints_authors',
                    kwargs={
                        'repository_short_name': request.repository.short_name,
                        'article_id': article.pk,
                    },
                ),
            )

    template = 'admin/preprints/submit/start.html'
    context = {
        'form': form,
        'article': article,
        'additional_fields': additional_fields,
    }

    return render(request, template, context)


@login_required
def preprints_authors(request, article_id):
    """
    Handles submission of new authors. Allows users to search
    for existing authors or add new ones.
    :param request: HttpRequest
    :param article_id: Article object PK
    :return: HttpRedirect or HttpResponse
    """
    preprint = get_object_or_404(
        models.Preprint,
        pk=article_id,
        repository=request.repository,
    )

    form = forms.AuthorForm()

    if request.POST:

        if 'self' in request.POST:
            author_preprint_created = preprint.add_user_as_author(
                request.user,
            )

            if not author_preprint_created:
                messages.add_message(
                    request,
                    messages.WARNING,
                    'This author is already associated with this {}'.format(
                        request.repository.object_name,
                    )
                )

        if 'search' in request.POST:
            repository_logic.search_for_authors(request, preprint)

        if 'form' in request.POST:
            form = forms.AuthorForm(request.POST)
            if form.is_valid():
                new_author = form.save()
                preprint_author, created = preprint.add_author(new_author)

                if not created:
                    messages.add_message(
                        request,
                        messages.WARNING,
                        '{} is already associated with this {}'.format(
                            preprint_author.author.full_name,
                            request.repository.object_name,
                        )
                    )

    template = 'admin/preprints/submit/authors.html'
    context = {
        'preprint': preprint,
        'form': form,
        'user_is_author': preprint.user_is_author(request.user),
    }

    return render(request, template, context)


@login_required
def preprints_files(request, article_id):
    """
    Allows authors to upload files to their preprint. Files are stored against the press in /files/preprints/
    File submission can be limited to PDF only.
    :param request: HttpRequest
    :param article_id: Article object PK
    :return: HttpRedirect or HttpResponse
    """
    article = get_object_or_404(submission_models.Article.preprints,
                                pk=article_id,
                                owner=request.user,
                                date_submitted__isnull=True)

    error, modal, form = None, None, submission_forms.FileDetails()

    if request.POST and 'delete' in request.POST:
        file_id = request.POST.get('delete')
        file = get_object_or_404(core_models.File, pk=file_id)
        file.unlink_file(journal=None)
        file.delete()
        messages.add_message(request, messages.WARNING, 'File deleted')
        return redirect(reverse('preprints_files', kwargs={'article_id': article_id}))

    if request.POST and request.FILES:

        form = submission_forms.FileDetails(request.POST)
        uploaded_file = request.FILES.get('file')

        # If required, check if the file is a PDF:
        if request.press.preprint_pdf_only and 'manuscript' in request.POST:
            if not files.check_in_memory_mime(in_memory_file=uploaded_file) == 'application/pdf':
                form.add_error(None, 'You must upload a PDF for your manuscript')
                modal = 'manuscript'

        # Check if the form is valid
        if form.is_valid():

            file = files.save_file_to_article(uploaded_file,
                                              article,
                                              request.user,
                                              form.cleaned_data['label'],
                                              form.cleaned_data['description'])

            if 'manuscript' in request.POST:
                article.manuscript_files.add(file)

            elif 'data' in request.POST:
                article.data_figure_files.add(file)

            messages.add_message(request, messages.INFO, 'File saved.')
            return redirect(reverse('preprints_files', kwargs={'article_id': article.pk}))

        # Handle displaying modals in event of an error:
        else:
            modal = repository_logic.get_display_modal(request)

    elif request.POST and 'next_step' in request.POST:
        return redirect(reverse('preprints_review', kwargs={'article_id': article.pk}))

    template = 'preprints/submit_files.html'
    context = {
        'article': article,
        'form': form,
        'modal': modal,
    }

    return render(request, template, context)


@login_required
def preprints_review(request, article_id):
    """
    Presents information for the user to review before completing the submission process.
    :param request: HttpRequest
    :param article_id: Article object PK
    :return: HttpRedirect or HttpResponse
    """
    article = get_object_or_404(submission_models.Article.preprints, pk=article_id,
                                owner=request.user,
                                date_submitted__isnull=True)

    if request.POST and 'next_step' in request.POST:
        # TODO: reduce this code to an article function submit_preprint?
        article.date_submitted = timezone.now()
        article.stage = submission_models.STAGE_PREPRINT_REVIEW
        article.current_step = 5
        article.save()

        kwargs = {'request': request, 'article': article}
        event_logic.Events.raise_event(event_logic.Events.ON_PREPRINT_SUBMISSION, **kwargs)

        messages.add_message(request, messages.SUCCESS, 'Article {0} submitted'.format(article.title))
        return redirect(reverse('repository_dashboard'))

    template = 'preprints/review.html'
    context = {
        'article': article,
    }

    return render(request, template, context)


@is_preprint_editor
def preprints_manager(request):
    """
    Displays preprint information and management interfaces for them.
    :param request: HttpRequest
    :return: HttpResponse or HttpRedirect
    """
    unpublished_preprints = repository_logic.get_unpublished_preprints(request)

    published_preprints = repository_logic.get_published_preprints(request)

    incomplete_preprints = submission_models.Article.preprints.filter(date_published__isnull=True,
                                                                      date_submitted__isnull=True)
    rejected_preprints = submission_models.Article.preprints.filter(date_declined__isnull=False)

    metrics_summary = repository_logic.metrics_summary(published_preprints)

    version_queue = models.VersionQueue.objects.filter(date_decision__isnull=True)

    subjects = models.Subject.objects.filter(enabled=True)

    template = 'admin/preprints/manager.html'
    context = {
        'unpublished_preprints': unpublished_preprints,
        'published_preprints': published_preprints,
        'incomplete_preprints': incomplete_preprints,
        'rejected_preprints': rejected_preprints,
        'version_queue': version_queue,
        'metrics_summary': metrics_summary,
        'subjects': subjects,
    }

    return render(request, template, context)


@is_article_preprint_editor
def preprints_manager_article(request, article_id):
    """
    Displays the metadata associated with the article and presents options for the editor to accept or decline the
    preprint, replace its files and set a publication date.
    :param request: HttpRequest object
    :param article_id: int, Article object PK
    :return: HttpResponse or HttpRedirect if successful POST.
    """
    preprint = get_object_or_404(submission_models.Article.preprints, pk=article_id)
    crossref_enabled = request.press.preprint_dois_enabled()

    if request.POST:

        if 'accept' in request.POST:
            if not preprint.has_galley:
                messages.add_message(request, messages.WARNING, 'You must assign at least one galley file.')
                return redirect(reverse('preprints_manager_article', kwargs={'article_id': preprint.pk}))
            else:
                date = request.POST.get('date', timezone.now().date())
                time = request.POST.get('time', timezone.now().time())
                doi = request.POST.get('doi', None)
                preprint.accept_preprint(date, time)

                if crossref_enabled and doi:
                    doi_obj = ident_logic.create_crossref_doi_identifier(article=preprint,
                                                                         doi_suffix=doi,
                                                                         suffix_is_whole_doi=True)
                    ident_logic.register_preprint_doi(request, crossref_enabled, doi_obj)
                    cache.clear()

                return redirect(reverse('preprints_notification', kwargs={'article_id': preprint.pk}))

        if 'decline' in request.POST:
            preprint.decline_article()
            return redirect(reverse('preprints_notification', kwargs={'article_id': preprint.pk}))

        if 'upload' in request.POST:
            repository_logic.handle_file_upload(request, preprint)
            return redirect(reverse('preprints_manager_article', kwargs={'article_id': preprint.pk}))

        if 'delete' in request.POST:
            repository_logic.handle_delete_version(request, preprint)
            return redirect(reverse('preprints_manager_article', kwargs={'article_id': preprint.pk}))

        if 'save_subject' in request.POST:
            repository_logic.handle_updating_subject(request, preprint)
            return redirect(reverse('preprints_manager_article', kwargs={'article_id': preprint.pk}))

        if 'unpublish' in request.POST:
            if preprint.date_published or request.user.is_staff:
                repository_logic.unpublish_preprint(request, preprint)
                return redirect(reverse('preprints_manager_article', kwargs={'article_id': preprint.pk}))

    template = 'admin/preprints/article.html'
    context = {
        'preprint': preprint,
        'subjects': models.Subject.objects.filter(enabled=True),
        'crossref_enabled': crossref_enabled,
        'doi': repository_logic.get_doi(request, preprint)
    }

    return render(request, template, context)


@is_article_preprint_editor
def preprints_notification(request, article_id):
    """
    Presents an interface for the preprint editor to notify an author of a decision.
    :param request: HttpRequest object
    :param article_id: int, Article object PK
    :return: HttpResponse or HttpRedirect
    """
    preprint = get_object_or_404(submission_models.Article.preprints, pk=article_id,
                                 preprint_decision_notification=False)
    action = repository_logic.determie_action(preprint)
    email_content = repository_logic.get_publication_text(request, preprint, action)

    if request.POST:
        email_content = request.POST.get('email_content', '')
        kwargs = {'request': request, 'article': preprint, 'email_content': email_content}
        event_logic.Events.raise_event(event_logic.Events.ON_PREPRINT_PUBLICATION, **kwargs)
        return redirect(reverse('preprints_manager_article', kwargs={'article_id': preprint.pk}))

    template = 'preprints/notification.html'
    context = {
        'action': action,
        'preprint': preprint,
        'email_content': email_content,
    }

    return render(request, template, context)


@preprint_editor_or_author_required
def preprints_comments(request, article_id):
    """
    Presents an interface for authors and editors to mark comments as publicly readable.
    :param request: HttpRequest object
    :param article_id: PK of an Article object
    :return: HttpRedirect if POST, HttpResponse otherwise
    """
    preprint = get_object_or_404(submission_models.Article.preprints, pk=article_id)

    if request.POST:
        repository_logic.comment_manager_post(request, preprint)
        return redirect(reverse('preprints_comments', kwargs={'article_id': preprint.pk}))

    template = 'admin/preprints/comments.html'
    context = {
        'preprint': preprint,
        'new_comments': preprint.comment_set.filter(is_reviewed=False),
        'old_comments': preprint.comment_set.filter(is_reviewed=True)
    }

    return render(request, template, context)


@staff_member_required
def preprints_settings(request):
    """
    Displays and allows editing of various prepprint settings
    :param request: HttpRequest
    :return: HttpRedirect if POST else HttpResponse
    """
    form = forms.SettingsForm(instance=request.press)

    if request.POST:
        form = forms.SettingsForm(request.POST, instance=request.press)

        if form.is_valid():
            form.save()
            return redirect(reverse('preprints_settings'))

    template = 'admin/preprints/settings.html'
    context = {
        'form': form,
    }

    return render(request, template, context)


@staff_member_required
def preprints_subjects(request, subject_id=None):

    if subject_id:
        subject = get_object_or_404(models.Subject, pk=subject_id)
    else:
        subject = None

    form = forms.SubjectForm(instance=subject)

    if request.POST:

        if 'delete' in request.POST:
            utils_shared.clear_cache()
            return repository_logic.handle_delete_subject(request)

        form = forms.SubjectForm(request.POST, instance=subject)

        if form.is_valid():
            form.save()
            utils_shared.clear_cache()
            return redirect(reverse('preprints_subjects'))

    template = 'admin/preprints/subjects.html'
    context = {
        'subjects': models.Subject.objects.all().prefetch_related('editors'),
        'form': form,
        'subject': subject,
        'active_users': core_models.Account.objects.all()
    }

    return render(request, template, context)


@staff_member_required
def preprints_rejected_submissions(request):
    """
    A staff only view that displays a list of preprints that have been rejected.
    :param request: HttpRequest object
    :return: HttpResponse
    """
    rejected_preprints = submission_models.Article.preprints.filter(date_declined__isnull=False,
                                                                    date_published__isnull=True)

    template = 'admin/preprints/rejected_submissions.html'
    context = {
        'rejected_preprints': rejected_preprints,
    }

    return render(request, template, context)


@staff_member_required
def orphaned_preprints(request):
    """
    Displays a list of preprints that have bee orphaned from subjects.
    :param request: HttpRequest object
    :return: HttpResponse
    """
    orphaned_preprints = repository_logic.list_articles_without_subjects()

    template = 'admin/preprints/orphaned_preprints.html'
    context = {
        'orphaned_preprints': orphaned_preprints
    }

    return render(request, template, context)


@staff_member_required
def version_queue(request):
    """
    Displays a list of version update requests.
    :param request: HttpRequest
    :return: HttpResponse or HttpRedirect
    """
    version_queue = models.VersionQueue.objects.filter(date_decision__isnull=True)
    duplicates = repository_logic.check_duplicates(version_queue)

    if request.POST:
        if 'approve' in request.POST:
            return repository_logic.approve_pending_update(request)
        elif 'deny' in request.POST:
            return repository_logic.deny_pending_update(request)

    template = 'admin/preprints/version_queue.html'
    context = {
        'version_queue': version_queue,
        'duplicates': duplicates,
    }

    return render(request, template, context)
