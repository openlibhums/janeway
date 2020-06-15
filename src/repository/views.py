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
from django.views.decorators.http import require_POST
from django.http import HttpResponse

from repository import forms, logic as repository_logic, models
from core import models as core_models, files
from metrics.logic import store_article_access
from utils import shared as utils_shared, logic as utils_logic
from events import logic as event_logic
from security.decorators import (
    preprint_editor_or_author_required,
    is_article_preprint_editor,
    is_preprint_editor,
)


def repository_home(request):
    """
    Displays the preprints home page with search box and 6 latest
    preprints publications
    :param request: HttpRequest object
    :return: HttpResponse
    """
    preprints = models.Preprint.objects.filter(
        repository=request.repository,
        date_published__lte=timezone.now(),
        stage=models.STAGE_PREPRINT_PUBLISHED
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
    preprints = models.Preprint.objects.filter(
        owner=request.user,
        date_submitted__isnull=False,
    )
    incomplete_preprints = models.Preprint.objects.filter(
        owner=request.user,
        date_submitted__isnull=True,
    )
    template = 'admin/repository/dashboard.html'
    context = {
        'preprints': preprints,
        'incomplete_preprints': incomplete_preprints,
    }

    return render(request, template, context)


@preprint_editor_or_author_required
def preprints_author_article(request, preprint_id):
    """
    Allows authors to view the metadata and replace galley files for their articles.
    :param request: HttpRequest
    :param preprint_id: Preprint PK
    :return: HttpRedirect if POST or HttpResponse
    """
    preprint = get_object_or_404(
        models.Preprint,
        pk=preprint_id,
        stage__in=models.SUBMITTED_STAGES,
    )
    metrics_summary = repository_logic.metrics_summary([preprint])

    # TODO: Reimplement this
    if request.POST:
        if 'submit' in request.POST:
            return repository_logic.handle_preprint_submission(request, preprint)
        else:
            repository_logic.handle_author_post(request, preprint)
            return redirect(
                reverse(
                    'preprints_author_article',
                    kwargs={'article_id': preprint.pk},
                )
            )

    template = 'admin/repository/author_article.html'
    context = {
        'preprint': preprint,
        'metrics_summary': metrics_summary,
        'preprint_journals': repository_logic.get_list_of_preprint_journals(),
        # TODO: FIX
        # 'pending_updates': models.VersionQueue.objects.filter(article=preprint, date_decision__isnull=True)
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


# TODO: Re-implement
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


# TODO: Re-implement
def repository_preprint(request, article_id):
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
            return redirect(reverse('repository_preprint', kwargs={'article_id': article_id}))

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


# TODO: Re-implement
def preprints_pdf(request, article_id):

    pdf_url = request.GET.get('file')

    template = 'preprints/pdf.html'
    context = {
        'pdf_url': pdf_url,
    }
    return render(request, template, context)


# TODO: Re-implement
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
    :param preprint_id: int Pk for a preprint object
    :return: HttpResponse or HttpRedirect
    """
    preprint = repository_logic.get_preprint_if_id(preprint_id)

    form = forms.PreprintInfo(
        instance=preprint,
        request=request,
    )

    if request.POST:
        form = forms.PreprintInfo(
            request.POST,
            instance=preprint,
            request=request,
        )

        if form.is_valid():
            preprint = form.save()
            return redirect(
                reverse(
                    'repository_authors',
                    kwargs={'preprint_id': preprint.pk},
                ),
            )

    template = 'admin/repository/submit/start.html'
    context = {
        'form': form,
        'preprint': preprint,
        'additional_fields': request.repository.additional_submission_fields(),
    }

    return render(request, template, context)


@login_required
def repository_authors(request, preprint_id):
    """
    Handles submission of new authors. Allows users to search
    for existing authors or add new ones.
    :param request: HttpRequest
    :param preprint_id: Preprint object PK
    :return: HttpRedirect or HttpResponse
    """
    preprint = get_object_or_404(
        models.Preprint,
        pk=preprint_id,
        repository=request.repository,
        owner=request.user,
        date_submitted__isnull=True,
    )
    form = forms.AuthorForm()
    modal, fire_redirect = None, False

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

            fire_redirect = True

        if 'search' in request.POST:
            repository_logic.search_for_authors(request, preprint)
            fire_redirect = True

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
                fire_redirect = True
            else:
                modal = 'newauthor'

        if 'complete' in request.POST:
            return redirect(
                reverse(
                    'repository_files',
                    kwargs={'preprint_id': preprint.pk}
                )
            )

        if fire_redirect:
            return redirect(
                reverse(
                    'repository_authors',
                    kwargs={
                        'preprint_id': preprint.pk,
                    }
                )
            )

    template = 'admin/repository/submit/authors.html'
    context = {
        'preprint': preprint,
        'form': form,
        'user_is_author': preprint.user_is_author(request.user),
        'modal': modal,
    }

    return render(request, template, context)


@login_required
def repository_files(request, preprint_id):
    """
    Allows authors to upload files to their preprint.
    Files are stored against the press in /files/preprints/
    File submission can be limited to PDF only.
    :param request: HttpRequest
    :param preprint_id: Preprint object PK
    :return: HttpRedirect or HttpResponse
    """
    preprint = get_object_or_404(
        models.Preprint,
        pk=preprint_id,
        repository=request.repository,
        owner=request.user,
        date_submitted__isnull=True,
    )

    form = forms.FileForm(preprint=preprint)

    if request.POST:

        if request.FILES:

            form = forms.FileForm(request.POST, request.FILES, preprint=preprint)
            uploaded_file = request.FILES.get('file')

            # If required, check if the file is a PDF:
            if request.repository.limit_upload_to_pdf:
                if not files.check_in_memory_mime(
                        in_memory_file=uploaded_file,
                ) == 'application/pdf':
                    form.add_error(None, 'You must upload a PDF for your manuscript')

            # Check if the form is valid
            if form.is_valid():
                file = form.save()
                preprint.submission_file = file
                preprint.submission_file.original_filename = request.FILES['file'].name
                preprint.submission_file.save()
                preprint.save()
                messages.add_message(request, messages.INFO, 'File saved.')
                return redirect(
                    reverse(
                        'repository_files',
                        kwargs={
                            'preprint_id': preprint.pk,
                        },
                    )
                )

        if 'complete' in request.POST:
            if preprint.submission_file:
                return redirect(
                    reverse(
                        'repository_review',
                        kwargs={'preprint_id': preprint.pk},
                    )
                )
            else:
                messages.add_message(
                    request,
                    messages.WARNING,
                    'You cannot complete this step without uploading a file.'
                )

    template = 'admin/repository/submit/files.html'
    context = {
        'preprint': preprint,
        'form': form,
    }

    return render(request, template, context)


@login_required
def repository_review(request, preprint_id):
    """
    Presents information for the user to review before completing
    the submission process.
    :param request: HttpRequest
    :param preprint_id: Preprint object PK
    :return: HttpRedirect or HttpResponse
    """
    preprint = get_object_or_404(
        models.Preprint,
        pk=preprint_id,
        owner=request.user,
        date_submitted__isnull=True,
    )

    if request.POST and 'complete' in request.POST:
        preprint.submit_preprint()
        kwargs = {'request': request, 'preprint': preprint}
        event_logic.Events.raise_event(
            event_logic.Events.ON_PREPRINT_SUBMISSION,
            **kwargs,
        )

        messages.add_message(
            request,
            messages.SUCCESS,
            '{object} {title} submitted'.format(
                object=request.repository.object_name,
                title=preprint.title
            )
        )
        return redirect(reverse('repository_dashboard'))

    template = 'admin/repository/submit/review.html'
    context = {
        'preprint': preprint,
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
    incomplete_preprints = models.Preprint.objects.filter(
        date_published__isnull=True,
        date_submitted__isnull=True,
    )
    rejected_preprints = models.Preprint.objects.filter(
        date_declined__isnull=False,
    )
    metrics_summary = repository_logic.metrics_summary(published_preprints)
    versisons = models.VersionQueue.objects.filter(
        date_decision__isnull=True,
    )
    subjects = models.Subject.objects.filter(enabled=True)

    template = 'admin/repository/manager.html'
    context = {
        'unpublished_preprints': unpublished_preprints,
        'published_preprints': published_preprints,
        'incomplete_preprints': incomplete_preprints,
        'rejected_preprints': rejected_preprints,
        'version_queue': versisons,
        'metrics_summary': metrics_summary,
        'subjects': subjects,
    }

    return render(request, template, context)


@is_article_preprint_editor
def repository_manager_article(request, preprint_id):
    """
    Displays the metadata associated with the article and presents
    options for the editor to accept or decline the
    preprint, replace its files and set a publication date.
    :param request: HttpRequest object
    :param preprint_id: int, Preprint object PK
    :return: HttpResponse or HttpRedirect if successful POST.
    """
    preprint = get_object_or_404(
        models.Preprint,
        pk=preprint_id,
        repository=request.repository,
    )
    crossref_enabled = request.press.preprint_dois_enabled()
    file_form = forms.FileForm(preprint=preprint)

    if request.POST:

        if 'accept' in request.POST:
            if not preprint.has_version():
                messages.add_message(
                    request,
                    messages.WARNING,
                    'You must assign at least one galley file.',
                )
            else:
                # TODO: Handle DOIs
                preprint.accept(
                    date=request.POST.get('date', timezone.now().date()),
                    time=request.POST.get('time', timezone.now().time()),
                )
                return redirect(
                    reverse(
                        'repository_notification',
                        kwargs={'preprint_id': preprint.pk},
                    )
                )

        if 'decline' in request.POST:
            preprint.decline()
            return redirect(
                reverse(
                    'repository_notification',
                    kwargs={'preprint_id': preprint.pk},
                )
            )

        if 'upload' in request.POST and request.FILES:
            file_form = forms.FileForm(
                request.POST,
                request.FILES,
                preprint=preprint,
            )

            if file_form.is_valid():
                file = file_form.save()
                file.original_filename = request.FILES['file'].name
                file.save()

        if 'delete_file' in request.POST:
            repository_logic.delete_file(request, preprint)

        if 'delete_version' in request.POST:
            repository_logic.handle_delete_version(request, preprint)

        if 'reset' in request.POST:
            if preprint.date_published or preprint.date_declined:
                preprint.reset()
                messages.add_message(
                    request,
                    messages.INFO,
                    'This preprint has been reset',
                )

        if 'make_version' in request.POST:
            file = get_object_or_404(
                models.PreprintFile,
                pk=request.POST.get('make_version'),
                preprint=preprint,
            )
            preprint.make_new_version(file)

        return redirect(
            reverse(
                'repository_manager_article',
                kwargs={'preprint_id': preprint.pk},
            )
        )

    template = 'admin/repository/article.html'
    context = {
        'preprint': preprint,
        'subjects': models.Subject.objects.filter(enabled=True),
        'crossref_enabled': crossref_enabled,
        # 'doi': repository_logic.get_doi(request, preprint)
        'file_form': file_form,
    }

    return render(request, template, context)


@is_article_preprint_editor
def repository_edit_metadata(request, preprint_id):
    """
    Presents an interface to edit a Preprint and related objects metadata
    :param request: HttpRequest
    :param preprint_id: Preprint PK
    :return: HttpReponse or HttpRedirtect
    """
    preprint = get_object_or_404(
        models.Preprint,
        pk=preprint_id,
        repository=request.repository
    )

    metadata_form = forms.PreprintInfo(
        instance=preprint,
        request=request,
    )

    author_formset = forms.AuthorFormSet(
        queryset=preprint.author_objects(),
    )

    fire_redirect = False

    if request.POST:
        if 'authors' in request.POST:
            author_formset = forms.AuthorFormSet(request.POST)
            if author_formset.is_valid():
                authors = author_formset.save()
                for author in authors:
                    models.PreprintAuthor.objects.get_or_create(
                        preprint=preprint,
                        author=author,
                        defaults={
                            'order': preprint.next_author_order(),
                        }
                    )
                fire_redirect = True

        if 'metadata' in request.POST:
            metadata_form = forms.PreprintInfo(
                request.POST,
                instance=preprint,
                request=request,
            )

            if metadata_form.is_valid():
                metadata_form.save()
                fire_redirect = True

        if fire_redirect:
            return redirect(
                reverse(
                    'repository_edit_metadata',
                    kwargs={'preprint_id': preprint.pk},
                )
            )

    template = 'admin/repository/edit_metadata.html'
    context = {
        'preprint': preprint,
        'metadata_form': metadata_form,
        'author_formset': author_formset,
        'additional_fields': request.repository.additional_submission_fields(),
    }

    return render(request, template, context)


@preprint_editor_or_author_required
def repository_download_file(request, preprint_id, file_id):
    """
    Serves files to preprint editors.
    :param request: HttpRequest
    :param preprint_id: Preprint PK int
    :param file_id: PreprintFile PK int
    :return: StreamingHttpResponse
    """
    preprint = get_object_or_404(
        models.Preprint,
        pk=preprint_id,
        repository=request.repository,
    )

    file = get_object_or_404(
        models.PreprintFile,
        pk=file_id,
        preprint=preprint,
    )

    return files.serve_any_file(
        request,
        file,
        path_parts=(file.path_parts(),)
    )


@is_article_preprint_editor
def repository_notification(request, preprint_id):
    """
    Presents an interface for the preprint editor to notify an author of a decision.
    :param request: HttpRequest object
    :param preprint_id: int, Preprint object PK
    :return: HttpResponse or HttpRedirect
    """
    preprint = get_object_or_404(
        models.Preprint,
        pk=preprint_id,
        repository=request.repository,
        preprint_decision_notification=False,
    )
    action = repository_logic.determine_action(preprint)
    email_content = repository_logic.get_publication_text(
        request,
        preprint,
        action,
    )

    if request.POST:
        email_content = request.POST.get('email_content', '')
        kwargs = {
            'request': request,
            'preprint': preprint,
            'email_content': email_content,
        }
        event_logic.Events.raise_event(
            event_logic.Events.ON_PREPRINT_PUBLICATION,
            **kwargs,
        )
        return redirect(
            reverse(
                'repository_manager_article',
                kwargs={'preprint_id': preprint.pk},
            )
        )

    template = 'admin/repository/notification.html'
    context = {
        'action': action,
        'preprint': preprint,
        'email_content': email_content,
    }

    return render(request, template, context)


@is_article_preprint_editor
def repository_preprint_log(request, preprint_id):
    """
    Displays log entries for a Preprint object.
    :param request: HttpRequest
    :param preprint_id: Preprint object PK
    :return: HttpResponse
    """
    preprint = get_object_or_404(
        models.Preprint,
        pk=preprint_id,
        repository=request.repository
    )
    log_entries = utils_logic.get_log_entries(preprint)
    print(log_entries)

    template = 'admin/repository/log.html'
    context = {
        'preprint': preprint,
        'log_entries': log_entries,
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


@login_required
@require_POST
def preprints_author_order(request, preprint_id):
    """
    Reorders preprint authors, used in AJAX calls.
    :param request: HttpRequest
    :param preprint_id: PK of a Preprint object
    :return: JSON OK
    """
    preprint = get_object_or_404(
        models.Preprint,
        pk=preprint_id,
        repository=request.repository,
        owner=request.user,
    )
    posted_author_pks = [int(pk) for pk in request.POST.getlist('authors[]')]
    preprint_authors = models.PreprintAuthor.objects.filter(
        preprint=preprint,
    )

    for preprint_author in preprint_authors:
        order = posted_author_pks.index(preprint_author.author.pk)
        author_order, c = models.PreprintAuthor.objects.get_or_create(
            preprint=preprint,
            author=preprint_author.author,
            defaults={'order': order}
        )

        if not c:
            author_order.order = order
            author_order.save()

    return HttpResponse('Complete')


@login_required
@require_POST
def preprints_delete_author(request, preprint_id, redirect_string):
    """
    Removes author-preprint link.
    :param request: HttpRequest object
    :param preprint_id: int, Preprint PK
    :return: HttpRedirect
    """
    author_id = request.POST.get('author_id')
    preprint = get_object_or_404(
        models.Preprint,
        pk=preprint_id,
        repository=request.repository,
        owner=request.user,
    )

    preprint_author = get_object_or_404(
        models.PreprintAuthor,
        author__id=author_id,
        preprint=preprint,
    )

    preprint_author.delete()

    messages.add_message(
        request,
        messages.INFO,
        'Author removed from {}'.format(
            request.repository.object_name,
        )
    )

    if redirect_string == 'submission':
        return redirect(
            reverse(
                'repository_authors',
                kwargs={
                    'preprint_id': preprint_id,
                }
            )
        )
    elif redirect_string == 'manager':
        return redirect(
            reverse(
                'repository_manager_article',
                kwargs={'preprint_id': preprint.pk},
            )
        )

