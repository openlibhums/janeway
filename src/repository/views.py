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
from django.http import HttpResponse, Http404
from django.core.exceptions import PermissionDenied

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
    )[:6]
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
def repository_author_article(request, preprint_id):
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
    file_form = forms.FileForm(preprint=preprint)
    version_form = forms.VersionForm(preprint=preprint)
    modal = None

    if request.POST:

        if request.FILES:

            file_form = forms.FileForm(
                request.POST,
                request.FILES,
                preprint=preprint,
            )
            version_form = forms.VersionForm(
                request.POST,
                preprint=preprint,
            )

            # If required, check if the file is a PDF:
            if request.repository.limit_upload_to_pdf:
                if not files.check_in_memory_mime(
                        in_memory_file=request.FILES.get('file'),
                ) == 'application/pdf':
                    file_form.add_error(
                        None,
                        'You must upload a PDF for your manuscript',
                    )

            if file_form.is_valid() and version_form.is_valid():
                new_file = file_form.save()
                new_version = version_form.save(commit=False)
                new_version.file = new_file
                new_version.save()

                return redirect(
                    reverse(
                        'repository_author_article',
                        kwargs={'preprint_id': preprint.pk},
                    )
                )
            modal = 'uploadbox'

    template = 'admin/repository/author_article.html'
    context = {
        'preprint': preprint,
        'metrics_summary': metrics_summary,
        'preprint_journals': repository_logic.get_list_of_preprint_journals(),
        'pending_updates': models.VersionQueue.objects.filter(
            preprint=preprint,
            date_decision__isnull=True,
        ),
        'file_form': file_form,
        'version_form': version_form,
        'modal': modal,
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
def repository_preprint(request, preprint_id):
    """
    Fetches a single article and displays its metadata
    :param request: HttpRequest
    :param preprint_id: integer, PK of an Article object
    :return: HttpResponse or Http404 if object not found
    """
    preprint = get_object_or_404(
        models.Preprint,
        pk=preprint_id,
        repository=request.repository,
        date_published__lte=timezone.now(),
    )
    comments = models.Comment.objects.filter(preprint=preprint, is_public=True)
    form = forms.CommentForm(
        preprint=preprint,
        author=request.user,
    )

    if request.POST:
        if not request.user.is_authenticated:
            messages.add_message(
                request,
                messages.WARNING,
                'You must be logged in to comment',
            )
            return redirect(reverse('core_login'))

        form = forms.CommentForm(
            request.POST,
            preprint=preprint,
            author=request.user,
        )

        if form.is_valid():
            comment = form.save()
            repository_logic.raise_comment_event(request, comment)
            return redirect(
                reverse(
                    'repository_preprint',
                    kwargs={'preprint_id': preprint.pk},
                )
            )

    # TODO: store access

    template = 'repository/preprint.html'
    context = {
        'preprint': preprint,
        'comments': comments,
        'form': form,
    }

    return render(request, template, context)

def repository_file_download(request, preprint_id, file_id):
    """
    Serves up a file for a published Preprint.
    """
    preprint = get_object_or_404(
        models.Preprint,
        pk=preprint_id,
        repository=request.repository,
        date_published__lte=timezone.now(),
    )

    file = get_object_or_404(
        models.PreprintFile,
        preprint=preprint,
        pk=file_id,
    )

    if file in preprint.version_files():
        return files.serve_any_file(
            request,
            file,
            path_parts=(file.path_parts(),)
        )

    raise PermissionDenied('You do not have permission to download this file.')


# TODO: Re-implement
def repository_pdf(request, preprint_id):

    pdf_url = request.GET.get('file')

    template = 'repository/pdf.html'
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
    modal, fire_redirect, author_to_add = None, False, None

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
                author_to_add = form.save()
            else:
                # If the form is not valid we want to grab the email address
                # and check if there is an author record already for that
                # author.
                if not form.cleaned_data.get('email_address', None):
                    email_address = form.data['email_address']
                    try:
                        author_to_add = models.Author.objects.get(
                            email_address=email_address,
                        )
                    except models.Author.DoesNotExist:
                        author_to_add = None

            if author_to_add:
                preprint_author, created = preprint.add_author(author_to_add)

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
    file_form = forms.FileForm(preprint=preprint)
    redirect_request, modal = False, None

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
                kwargs = {
                    'date': request.POST.get('date', timezone.now().date()),
                    'time': request.POST.get('time', timezone.now().time()),
                }
                if preprint.date_published:
                    preprint.update_date_published(**kwargs)
                else:
                    preprint.accept(**kwargs)
                    return redirect(
                        reverse(
                            'repository_notification',
                            kwargs={'preprint_id': preprint.pk},
                        )
                    )

            redirect_request = True

        if 'decline' in request.POST:
            preprint.decline()
            redirect_request = True

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
                redirect_request = True
            else:
                modal = 'new_file'

        if 'delete_file' in request.POST:
            repository_logic.delete_file(request, preprint)
            redirect_request = True

        if 'delete_version' in request.POST:
            repository_logic.handle_delete_version(request, preprint)
            redirect_request = True

        if 'reset' in request.POST:
            if preprint.date_published or preprint.date_declined:
                preprint.reset()
                messages.add_message(
                    request,
                    messages.INFO,
                    'This preprint has been reset',
                )
                redirect_request = True

        if 'make_version' in request.POST:
            file = get_object_or_404(
                models.PreprintFile,
                pk=request.POST.get('make_version'),
                preprint=preprint,
            )
            preprint.make_new_version(file)
            redirect_request = True

        if redirect_request:
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
        'file_form': file_form,
        'pending_updates': models.VersionQueue.objects.filter(
            preprint=preprint,
            date_decision__isnull=True,
        ),
        'modal': modal,
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

        if 'delete_author' in request.POST:
            author_id = request.POST.get('delete_author')
            print(author_id)
            author = get_object_or_404(
                models.PreprintAuthor,
                author__pk=author_id,
                preprint=preprint,
            ).delete()
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

    template = 'admin/repository/log.html'
    context = {
        'preprint': preprint,
        'log_entries': log_entries,
    }

    return render(request, template, context)


@preprint_editor_or_author_required
def repository_comments(request, preprint_id):
    """
    Presents an interface for authors and editors to mark comments as publicly readable.
    :param request: HttpRequest object
    :param preprint_id: PK of an Preprint object
    :return: HttpRedirect if POST, HttpResponse otherwise
    """
    preprint = get_object_or_404(models.Preprint.objects, pk=preprint_id)

    if request.POST:
        repository_logic.comment_manager_post(request, preprint)
        return redirect(
            reverse(
                'repository_comments', kwargs={'preprint_id': preprint.pk},
            )
        )

    template = 'admin/repository/comments.html'
    context = {
        'preprint': preprint,
        'new_comments': preprint.comment_set.filter(is_reviewed=False),
        'old_comments': preprint.comment_set.filter(is_reviewed=True)
    }

    return render(request, template, context)


@staff_member_required
def repository_subjects(request, subject_id=None):

    subject, parent_subject, initial = None, None, {}

    if subject_id:
        subject = get_object_or_404(
            models.Subject,
            pk=subject_id,
            repository=request.repository,
        )

    if request.GET.get('parent'):
        parent_subject = get_object_or_404(
            models.Subject,
            slug=request.GET.get('parent'),
            repository=request.repository,
        )
        initial = {'parent': parent_subject}

    form = forms.SubjectForm(
        instance=subject,
        repository=request.repository,
        initial=initial,
    )

    if request.POST:
        form = forms.SubjectForm(
            request.POST,
            instance=subject,
            repository=request.repository,
        )

        if form.is_valid():
            form.save()
            form.save_m2m()
            utils_shared.clear_cache()
            return redirect(reverse('repository_subjects'))

    top_level_subjects = models.Subject.objects.filter(
        parent__isnull=True,
    ).prefetch_related('editors')

    template = 'admin/repository/subjects.html'
    context = {
        'top_level_subjects': top_level_subjects,
        'form': form,
        'subject': subject,
        'active_users': core_models.Account.objects.all()
    }

    return render(request, template, context)


@require_POST
@staff_member_required
def repository_delete_subject(request):
    subject_id = request.POST.get('delete')
    subject = get_object_or_404(
        models.Subject,
        pk=subject_id,
        repository=request.repository,
    )
    subject.delete()

    messages.add_message(
        request,
        messages.SUCCESS,
        'Subject deleted. Any associated articles will have been orphaned.'
    )

    return redirect(
        reverse('repository_subjects')
    )


@staff_member_required
def repository_rejected_submissions(request):
    """
    A staff only view that displays a list of preprints that have been
    rejected.
    :param request: HttpRequest object
    :return: HttpResponse
    """
    rejected_preprints = models.Preprint.objects.filter(
        date_declined__isnull=False,
        date_published__isnull=True,
    )

    template = 'admin/repository/rejected_submissions.html'
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

    template = 'admin/repository/orphaned_preprints.html'
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
    version_queue = models.VersionQueue.objects.filter(
        date_decision__isnull=True,
    )
    duplicates = repository_logic.check_duplicates(version_queue)

    if request.POST:
        if 'approve' in request.POST:
            return repository_logic.approve_pending_update(request)
        elif 'decline' in request.POST:
            return repository_logic.decline_pending_update(request)

    template = 'admin/repository/version_queue.html'
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
def repository_delete_author(request, preprint_id, redirect_string):
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


@staff_member_required
def repository_wizard(request, short_name=None, step='1'):
    """
    Presents a Wizard for setting up new Repositories.
    :param request: HttpRequest
    :param short_name: str Repository object short_name
    :param step: String Number from 1-4
    :return: HttpResponse or HttpRedirect on POST
    """
    if short_name:
        repository = get_object_or_404(
            models.Repository,
            short_name=short_name,
        )
    elif request.repository:
        repository = request.repository
    else:
        repository = None

    if step == '1':
        form_type = forms.RepositoryInitial
    elif step == '2':
        form_type = forms.RepositorySite
    elif step == '3':
        form_type = forms.RepositorySubmission
    elif step == '4':
        form_type = forms.RepositoryEmails
    elif step == '5':
        form_type = forms.RepositoryLiveForm
    else:
        raise Http404

    form = form_type(instance=repository, press=request.press)

    if request.POST:
        form = form_type(
            request.POST,
            request.FILES,
            instance=repository,
            press=request.press,
        )

        if form.is_valid():
            updated_repository = form.save()

            # If we reach step 4, redirect to the Repo home page.
            if step == '5':
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    '{} has been setup.'.format(updated_repository.name)
                )
                return redirect(
                    reverse(
                        'core_manager_index'
                    )
                )

            # Bump the step by 1
            kwargs = {'step': int(step) + 1}
            if updated_repository:
                kwargs['short_name'] = updated_repository.short_name
            return redirect(
                reverse(
                    'repository_wizard_with_id',
                    kwargs=kwargs,
                )
            )

    template = 'admin/repository/wizard.html'
    context = {
        'repository': repository,
        'form': form,
        'step': step,
        'help_template': 'admin/elements/repository/{step}_help.html'.format(
            step=step,
        )
    }

    return render(request, template, context)

