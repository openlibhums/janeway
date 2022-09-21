__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import operator

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
from django.utils.translation import ugettext_lazy as _

from repository import forms, logic as repository_logic, models
from core import models as core_models, files, logic as core_logic, forms as core_forms
from journal import models as journal_models
from submission import models as submission_models


from utils import (
  logger,
  logic as utils_logic,
  models as utils_models,
  shared as utils_shared,
)
from events import logic as event_logic
from security.decorators import (
    preprint_editor_or_author_required,
    is_article_preprint_editor,
    is_repository_manager,
    submission_authorised,
)


logger = logger.get_logger(__name__)


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
        stage=models.STAGE_PREPRINT_PUBLISHED,
    ).order_by('-date_published')[:6]
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


def repository_sitemap(request, subject_id=None):
    """
    :param request: HttpRequest object
    :return: HttpResponse
    """
    try:
        if subject_id:
            subject = get_object_or_404(
                models.Subject,
                pk=subject_id,
                repository=request.repository,
            )
            path_parts = [
                request.repository.code,
                '{}_sitemap.xml'.format(subject.pk),
            ]
        else:
            path_parts = [
                request.repository.code,
                'sitemap.xml',
            ]

        if path_parts:
            return files.serve_sitemap_file(path_parts)
    except FileNotFoundError:
        logger.warning('Sitemap for {} not found.'.format(request.repository.name))

    raise Http404()


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
        repository=request.repository,
    )
    incomplete_preprints = models.Preprint.objects.filter(
        owner=request.user,
        date_submitted__isnull=True,
        repository=request.repository,
    )

    if request.POST and 'delete' in request.POST:
        preprint_id = request.POST.get('delete')
        if preprint_id:
            try:
                preprint = models.Preprint.objects.get(
                    pk=preprint_id,
                    owner=request.user,
                    stage=models.STAGE_PREPRINT_UNSUBMITTED,
                    repository=request.repository,
                )
                preprint.delete()
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    '{} deleted.'.format(request.repository.object_name),
                )
            except models.Preprint.DoesNotExist:
                messages.add_message(
                    request,
                    messages.WARNING,
                    'No incomplete {} found matching the ID supplied and owned by the current user.'.format(
                        request.repository.object_name,
                    )
                )
        return redirect(
            reverse(
                'repository_dashboard',
            )
        )

    template = 'admin/repository/dashboard.html'
    context = {
        'preprints': preprints,
        'incomplete_preprints': incomplete_preprints,
    }

    return render(request, template, context)
    

@preprint_editor_or_author_required
def repository_submit_update(request, preprint_id, action):
    """
    Allows a preprint author to update their Preprint.
    :param request: HttpRequest
    :param preprint_id: Preprint PK
    :param action: String, correction, version or metadata_correction
    """
    preprint = get_object_or_404(
        models.Preprint,
        pk=preprint_id,
        stage__in=models.SUBMITTED_STAGES,
        repository=request.repository,
    )

    file_form = None
    version_form = forms.VersionForm(preprint=preprint)
    
    if action in ['correction', 'version']:
        file_form = forms.FileForm(preprint=preprint)

    if request.POST:
        version_form = forms.VersionForm(
            request.POST,
            preprint=preprint,
        )
        if action in ['correction', 'version'] and request.FILES:
            file_form = forms.FileForm(
                request.POST,
                request.FILES,
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
        if version_form.is_valid() and (file_form.is_valid() if file_form else True):
            new_version = version_form.save(commit=False)
            new_version.update_type = action

            if file_form:
                new_file = file_form.save()
                new_version.file = new_file

            new_version.save()

            return redirect(
                reverse(
                    'repository_author_article',
                    kwargs={'preprint_id': preprint.pk},
                )
            )

    template = 'admin/repository/submit_update.html'
    context = {
        'preprint': preprint,
        'action': action,
        'version_form': version_form,
        'file_form': file_form,
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
        repository=request.repository,
    )
    metrics_summary = repository_logic.metrics_summary([preprint])

    template = 'admin/repository/author_article.html'
    context = {
        'preprint': preprint,
        'metrics_summary': metrics_summary,
        'preprint_journals': repository_logic.get_list_of_preprint_journals(),
        'pending_updates': models.VersionQueue.objects.filter(
            preprint=preprint,
            date_decision__isnull=True,
        ),
    }

    return render(request, template, context)


def repository_about(request):
    """
    Displays the about page with text about preprints
    :param request: HttpRequest object
    :return: HttpResponse
    """
    template = 'repository/about.html'
    return render(request, template, {})


def repository_subject_list(request):
    """
    Displays a list of enabled subjects for selection.
    :param request: a HttpRequest object
    :return: HttpResponse
    """
    top_level_subjects = models.Subject.objects.filter(
        repository=request.repository,
        enabled=True,
        parent__isnull=True,
    )
    
    template = 'repository/list_subjects.html'
    context = {
        'top_level_subjects': top_level_subjects,
    }
    return render(request, template, context)



def repository_list(request, subject_id=None):
    """
    Displays a list of all published preprints.
    :param request: HttpRequest
    :return: HttpResponse
    """
    if subject_id:
        subject = get_object_or_404(
            models.Subject,
            pk=subject_id,
            repository=request.repository,
        )
        preprints = subject.preprint_set.filter(
            repository=request.repository,
            date_published__lte=timezone.now(),
        ).order_by('-date_published')
    else:
        subject = None
        preprints = models.Preprint.objects.filter(
            date_published__lte=timezone.now(),
            repository=request.repository,
        ).order_by('-date_published')

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
        'subjects': models.Subject.objects.filter(enabled=True),
    }

    return render(request, template, context)


def repository_search(request, search_term=None):
    """
    Searches for and displays a list of Preprints.
    """
    if request.POST and 'search_term' in request.POST:
        search_term = request.POST.get('search_term')
        return redirect(
            reverse(
                'repository_search_with_term',
                kwargs={'search_term': search_term},
            )
        )

    # Grab all of the preprints that are published. We can then filter them
    # if a search term is given or return them if none.
    preprints = models.Preprint.objects.filter(
        date_published__lte=timezone.now(),
        repository=request.repository,
    )

    if search_term:
        split_search_term = search_term.split(' ')

        # Initial filter on Title, Abstract and Keywords.
        preprint_search = preprints.filter(
            (Q(title__icontains=search_term) |
             Q(abstract__icontains=search_term) |
             Q(keywords__word__in=split_search_term))
        )

        from_author = models.PreprintAuthor.objects.filter(
            (
                    Q(author__first_name__in=split_search_term) |
                    Q(author__middle_name__in=split_search_term) |
                    Q(author__last_name__in=split_search_term) |
                    Q(author__affiliation__icontains=search_term)
            )
        )

        preprints_from_author = [pa.preprint for pa in models.PreprintAuthor.objects.filter(
            pk__in=from_author,
            preprint__date_published__lte=timezone.now(),
        )]

        preprints = list(set(list(preprint_search) + preprints_from_author))
        preprints.sort(key=operator.attrgetter('date_published'), reverse=True)

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
        'search_term': search_term,
        'preprints': preprints,
    }

    return render(request, template, context)


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

    repository_logic.store_preprint_access(
        request,
        preprint,
    )

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
        if not request.GET.get('embed'):
            # When the file is embedded we do not count this as a Download.
            repository_logic.store_preprint_access(
                request,
                preprint,
                file,
            )
        return files.serve_any_file(
            request,
            file,
            path_parts=(file.path_parts(),)
        )

    raise PermissionDenied('You do not have permission to download this file.')


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
    subjects = models.Subject.objects.filter(
        repository=request.repository,
        enabled=True,
    )

    template = 'preprints/editors.html'
    context = {
        'subjects': subjects,
    }

    return render(request, template, context)


@submission_authorised
def repository_submit(request, preprint_id=None):
    """
    Handles initial steps of generating a preprints submission.
    :param request: HttpRequest
    :param preprint_id: int Pk for a preprint object
    :return: HttpResponse or HttpRedirect
    """
    if preprint_id:
        preprint = get_object_or_404(
            models.Preprint,
            pk=preprint_id,
            date_submitted__isnull=True,
            repository=request.repository,
        )
    else:
        preprint = None

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


@submission_authorised
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
    form = forms.AuthorForm(
        instance=None,
        request=request,
        preprint=preprint,
    )
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
            form = forms.AuthorForm(
                request.POST,
                request=request,
                preprint=preprint,
                instance=None,
            )

            if form.is_valid():
                form.save()
                fire_redirect = True
            else:
                modal = 'newauthor'

        if 'complete' in request.POST:
            if preprint.authors:
                return redirect(
                    reverse(
                        'repository_files',
                        kwargs={'preprint_id': preprint.pk}
                    )
                )
            messages.add_message(
                request,
                messages.WARNING,
                'You must add at least one author.',
            )
            fire_redirect = True

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


@submission_authorised
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
    supplementary = forms.PreprintSupplementaryFileForm(
        preprint=preprint,
    )

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

        if 'label' and 'url' in request.POST:
            supplementary = forms.PreprintSupplementaryFileForm(
                request.POST,
                preprint=preprint,
            )
            if supplementary.is_valid():
                preprint_supplementary, created = preprint.add_supplementary_file(supplementary)
                messages.add_message(request, messages.INFO, 'Supplementary file link saved.')

        if 'complete' in request.POST:
            if preprint.submission_file:
                preprint.submit_preprint()
                kwargs = {'request': request, 'preprint': preprint}
                event_logic.Events.raise_event(
                    event_logic.Events.ON_PREPRINT_SUBMISSION,
                    **kwargs,
                )

                messages.add_message(
                    request,
                    messages.SUCCESS,
                    '{object} {title} submitted.'.format(
                        object=request.repository.object_name,
                        title=preprint.title
                    )
                )
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
        'supplementary': supplementary,
    }

    return render(request, template, context)


@submission_authorised
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
        date_submitted__isnull=False,
        repository=request.repository,
    )

    if request.POST and 'complete' in request.POST:

        return redirect(reverse('repository_dashboard'))

    template = 'admin/repository/submit/review.html'
    context = {
        'preprint': preprint,
    }

    return render(request, template, context)


@is_repository_manager
def preprints_manager(request):
    """
    Displays preprint information and management interfaces for them.
    :param request: HttpRequest
    :return: HttpResponse or HttpRedirect
    """
    user_subject_pks = repository_logic.subject_article_pks(request.user)
    unpublished_preprints = repository_logic.get_unpublished_preprints(
        request,
        user_subject_pks,
    )
    published_preprints = repository_logic.get_published_preprints(
        request,
        user_subject_pks,
    )
    incomplete_preprints = models.Preprint.objects.filter(
        date_published__isnull=True,
        date_submitted__isnull=True,
        repository=request.repository,
    )
    rejected_preprints = models.Preprint.objects.filter(
        date_declined__isnull=False,
        repository=request.repository,
    )
    metrics_summary = repository_logic.metrics_summary(published_preprints)
    versisons = models.VersionQueue.objects.filter(
        date_decision__isnull=True,
        preprint__repository=request.repository,
    )
    subjects = models.Subject.objects.filter(
        repository=request.repository,
        enabled=True,
    )

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
                date_kwargs = {
                    'date': request.POST.get('date', timezone.now().date()),
                    'time': request.POST.get('time', timezone.now().time()),
                }
                if preprint.date_published:
                    preprint.update_date_published(**date_kwargs)
                else:
                    preprint.accept(**date_kwargs)
                    event_logic.Events.raise_event(
                        event_logic.Events.ON_PREPRINT_PUBLICATION,
                        **{
                            'request': request,
                            'preprint': preprint,
                        },
                    )
                    return redirect(
                        reverse(
                            'repository_notification',
                            kwargs={'preprint_id': preprint.pk},
                        )
                    )

            redirect_request = True

        if 'decline' in request.POST:
            note = request.POST.get('decline_note')
            preprint.decline(note=note)
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
                utils_models.LogEntry.add_entry(
                    'Reset',
                    'Decision Reset for {}'.format(preprint.title),
                    'Info',
                    request.user,
                    request,
                    preprint,
                )
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
        'comment_count': preprint.comment_set.filter(
            review__isnull=True,
        ).count()
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
        admin=True,
    )

    if request.POST:
        if 'metadata' in request.POST:
            metadata_form = forms.PreprintInfo(
                request.POST,
                instance=preprint,
                request=request,
                admin=True,
            )

            if metadata_form.is_valid():
                metadata_form.save()

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
        'additional_fields': request.repository.additional_submission_fields(),
    }

    return render(request, template, context)


@is_article_preprint_editor
def repository_edit_author(request, preprint_id, author_id=None):
    preprint = get_object_or_404(
        models.Preprint,
        pk=preprint_id,
        repository=request.repository
    )
    author = get_object_or_404(
        models.PreprintAuthor,
        pk=author_id,
        preprint=preprint,
    ) if author_id else None

    form = forms.AuthorForm(
        instance=author,
        preprint=preprint,
        request=request,
    )

    if request.POST:

        if 'search' in request.POST:
            author_save = repository_logic.search_for_authors(request, preprint)
        else:
            form = forms.AuthorForm(
                request.POST,
                instance=author,
                preprint=preprint,
                request=request,
            )
            if form.is_valid():
                author_save = form.save()
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    _('Author information saved'),
                )
        if author_save:
            return redirect(
                reverse('repository_edit_authors', args=[preprint.pk, author_save.pk])
            )

    template = 'admin/repository/edit_authors.html'
    context = {
        'preprint': preprint,
        'form': form,
        'author': author,
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
            'skip': True if 'skip' in request.POST else False,
        }
        event_logic.Events.raise_event(
            event_logic.Events.ON_PREPRINT_NOTIFICATION,
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
    preprint = get_object_or_404(
        models.Preprint.objects,
        pk=preprint_id,
        repository=request.repository,
    )

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
        'new_comments': preprint.comment_set.filter(
            is_reviewed=False,
            review__isnull=True,
        ),
        'old_comments': preprint.comment_set.filter(
            is_reviewed=True,
            review__isnull=True,
        )
    }

    return render(request, template, context)


@is_repository_manager
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
        repository=request.repository,
    ).prefetch_related('editors')

    template = 'admin/repository/subjects.html'
    context = {
        'top_level_subjects': top_level_subjects,
        'form': form,
        'subject': subject,
        'active_users': core_models.Account.objects.filter(is_active=True),
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
        'Subject deleted. Any associated articles will have been orphaned.',
    )

    return redirect(
        reverse('repository_subjects')
    )


@is_repository_manager
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
        repository=request.repository,
    )

    template = 'admin/repository/rejected_submissions.html'
    context = {
        'rejected_preprints': rejected_preprints,
    }

    return render(request, template, context)


@is_repository_manager
def orphaned_preprints(request):
    """
    Displays a list of preprints that have bee orphaned from subjects.
    :param request: HttpRequest object
    :return: HttpResponse
    """
    orphaned_preprints = repository_logic.list_articles_without_subjects(
        request.repository,
    )

    template = 'admin/repository/orphaned_preprints.html'
    context = {
        'orphaned_preprints': orphaned_preprints,
    }

    return render(request, template, context)


@is_repository_manager
def version_queue(request):
    """
    Displays a list of version update requests.
    :param request: HttpRequest
    :return: HttpResponse or HttpRedirect
    """
    version_queue = models.VersionQueue.objects.filter(
        date_decision__isnull=True,
        preprint__repository=request.repository,
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
    preprint = None
    try:
        preprint = models.Preprint.objects.get(
            pk=preprint_id,
            repository=request.repository,
            owner=request.user,
        )
    except models.Preprint.DoesNotExist:
        try:
            preprint = models.Preprint.objects.get(
                pk=preprint_id,
                repository=request.repository,
                repository__managers=request.user,
            )
        except models.Preprint.DoesNotExist:
            pass

    if not preprint:
        raise PermissionDenied(
            'Permission Denied. You must be the owner or a repository manager.',
        )

    posted_author_pks = [int(pk) for pk in request.POST.getlist('authors[]')]
    preprint_authors = models.PreprintAuthor.objects.filter(
        preprint=preprint,
    )

    for preprint_author in preprint_authors:
        order = posted_author_pks.index(preprint_author.pk)
        author_order, c = models.PreprintAuthor.objects.get_or_create(
            preprint=preprint,
            account=preprint_author.account,
            defaults={'order': order},
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

    if redirect_string == 'submission':
        # Checks the user is the owner of the Preprint.
        preprint = get_object_or_404(
            models.Preprint,
            pk=preprint_id,
            repository=request.repository,
            owner=request.user,
        )
    else:
        # Checks if user in a Repository managers m2m.
        preprint = get_object_or_404(
            models.Preprint,
            pk=preprint_id,
            repository=request.repository,
            repository__managers=request.user,
        )

    preprint_author = get_object_or_404(
        models.PreprintAuthor,
        pk=author_id,
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


@is_repository_manager
def repository_fields(request, field_id=None):
    """
    Allows repository managers to manage additional fields.
    """
    if field_id:
        field = get_object_or_404(
            models.RepositoryField,
            repository=request.repository,
            pk=field_id,
        )
    else:
        field = None

    form = forms.RepositoryFieldForm(
        instance=field,
        repository=request.repository,
    )

    if request.POST:
        form = forms.RepositoryFieldForm(
            request.POST,
            instance=field,
            repository=request.repository,
        )

        if form.is_valid():
            form.save()
            messages.add_message(
                request,
                messages.SUCCESS,
                'Field Saved.',
            )

            return redirect(
                reverse(
                    'repository_fields',
                )
            )

    template = 'admin/repository/fields.html'
    context = {
        'field': field,
        'form': form,
        'fields': request.repository.additional_submission_fields(),
    }

    return render(request, template, context)


@require_POST
@is_repository_manager
def repository_delete_field(request):
    """
    Deletes a Repositories field.
    """
    field_id = request.POST.get('field_to_delete')
    field = get_object_or_404(
        models.RepositoryField,
        repository=request.repository,
        pk=field_id,
    )
    field.delete()
    messages.add_message(
        request,
        messages.WARNING,
        'Field Deleted.'
    )

    return redirect(
        reverse('repository_fields')
    )


@require_POST
@is_repository_manager
def repository_order_fields(request):
    ids = [int(_id) for _id in request.POST.getlist('fields[]')]

    for field in request.repository.additional_submission_fields():
        field.order = ids.index(field.pk)
        field.save()

    return HttpResponse('Ok')


@preprint_editor_or_author_required
def manage_supplementary_files(request, preprint_id):
    preprint = get_object_or_404(
        models.Preprint,
        pk=preprint_id,
        repository=request.repository,
    )
    form = forms.PreprintSupplementaryFileForm(
        preprint=preprint,
    )
    template = 'admin/repository/manage_supp_files.html'
    if preprint.owner == request.user and not request.user in request.repository.managers.all():
        template = 'admin/repository/author_supp_files.html'
    context = {
        'preprint': preprint,
        'supplementary_files': preprint.supplementaryfiles,
        'form': form,
    }
    return render(request, template, context)


@require_POST
@preprint_editor_or_author_required
def new_supplementary_file(request, preprint_id):
    preprint = get_object_or_404(
        models.Preprint,
        pk=preprint_id,
        repository=request.repository,
    )
    if 'form' in request.POST:
        form = forms.PreprintSupplementaryFileForm(
            request.POST,
            preprint=preprint,
        )
        if form.is_valid():
            preprint.add_supplementary_file(
                form,
            )
            messages.add_message(
                request,
                messages.SUCCESS,
                'New Supplementary File Created',
            )
        else:
            messages.add_message(
                request,
                messages.WARNING,
                ' '.join([' '.join(x for x in l) for l in list(form.errors.values())])
            )
    else:
        messages.add_message(
            request,
            messages.INFO,
            'No form supplied.',
        )
    return redirect(
        reverse(
            'repository_manage_supplementary_files',
            kwargs={'preprint_id': preprint.pk},
        )
    )


@require_POST
@preprint_editor_or_author_required
def order_supplementary_files(request, preprint_id):
    preprint = get_object_or_404(
        models.Preprint,
        pk=preprint_id,
        repository=request.repository,
    )
    if 'contact[]' in request.POST:
        ids = [int(_id) for _id in request.POST.getlist('contact[]')]

        for file in preprint.supplementaryfiles:
            file.order = ids.index(file.pk)
            file.save()

    return HttpResponse('Ok')


@require_POST
@preprint_editor_or_author_required
def delete_supplementary_file(request, preprint_id):
    preprint = get_object_or_404(
        models.Preprint,
        pk=preprint_id,
        repository=request.repository,
    )
    try:
        id_to_delete = int(request.POST.get('delete', 0))
    except ValueError:
        raise ValueError(
            'The Supplementary File ID must be an integer.',
        )

    file_to_delete = get_object_or_404(
        models.PreprintSupplementaryFile,
        pk=id_to_delete,
        preprint=preprint,
    )
    file_to_delete.delete()
    messages.add_message(
        request,
        messages.SUCCESS,
        'Supplementary file deleted',
    )
    return redirect(
        reverse(
            'repository_manage_supplementary_files',
            kwargs={'preprint_id': preprint.pk},
        )
    )


@is_repository_manager
@require_POST
def reorder_preprint_authors(request, preprint_id):
    preprint = models.Preprint.objects.get(
        pk=preprint_id,
        repository=request.repository,
    )
    posted_author_pks = [int(pk) for pk in request.POST.getlist('authors[]')]
    preprint_authors = models.PreprintAuthor.objects.filter(
        preprint=preprint,
    )
    utils_shared.set_order(
        objects=preprint_authors,
        order_attr_name='order',
        pk_list=posted_author_pks,
    )
    return HttpResponse('Author Order Updated')


@is_repository_manager
@require_POST
def delete_preprint_author(request, preprint_id):
    preprint = models.Preprint.objects.get(
        pk=preprint_id,
        repository=request.repository,
    )

    if 'author_id' in request.POST:
        try:
            author = models.PreprintAuthor.objects.get(
                preprint=preprint,
                pk=request.POST.get('author_id'),
            )
            author.delete()
            messages.add_message(
                request,
                messages.SUCCESS,
                'Author record deleted.',
            )
        except models.PreprintAuthor.DoesNotExist:
            messages.add_message(
                request,
                messages.WARNING,
                'No author found.',
            )

    return redirect(
        reverse(
            'repository_manager_article',
            kwargs={'preprint_id': preprint.pk},
        )
    )


@is_repository_manager
def send_preprint_to_journal(request, preprint_id, journal_id=None):
    preprint = get_object_or_404(
        models.Preprint,
        pk=preprint_id,
        repository=request.repository,
    )
    if journal_id:
        journal = get_object_or_404(
            journal_models.Journal,
            pk=journal_id,
        )
    else:
        journal = None

    form = forms.PreprinttoArticleForm(
        journal=journal,
    )

    if request.POST:
        form = forms.PreprinttoArticleForm(
            request.POST,
            journal=journal,
        )
        if form.is_valid():
            article = preprint.create_article(
                journal=journal,
                workflow_stage=form.cleaned_data.get('stage'),
                journal_license=form.cleaned_data.get('license'),
                journal_section=form.cleaned_data.get('section'),
                force=form.cleaned_data.get('force'),
            )
            if article:
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    'Article {} created in journal {}'.format(
                        article.pk,
                        journal.name,
                    )
                )
            else:
                messages.add_message(
                    request,
                    messages.WARNING,
                    'No article created.',
                )

            return redirect(
                reverse(
                    'repository_manager_article',
                    kwargs={'preprint_id': preprint.pk},
                )
            )

    template = 'repository/send_preprint_to_journal.html'
    context = {
        'preprint': preprint,
        'journal': journal,
        'form': form,
        'journals': journal_models.Journal.objects.all().order_by('code'),
    }
    return render(
        request,
        template,
        context,
    )


# Repository Review
@is_repository_manager
def list_reviews(request, preprint_id):
    """
    For a given preprint list active reviews.
    """
    preprint = get_object_or_404(
        models.Preprint,
        pk=preprint_id,
        repository=request.repository,
    )
    active_reviews = models.Review.objects.filter(
        preprint=preprint,
    ).exclude(
        status__in=['declined', 'withdrawn']
    )
    inactive_reviews = models.Review.objects.filter(
        preprint=preprint,
        status__in=['declined', 'withdrawn']
    )
    template = 'repository/review/list_reviews.html'
    context = {
        'preprint': preprint,
        'active_reviews': active_reviews,
        'inactive_reviews': inactive_reviews,
    }
    return render(
        request,
        template,
        context,
    )


@is_repository_manager
def review_detail(request, preprint_id, review_id):
    """
    Displays detailed information about a review.
    """
    preprint = get_object_or_404(
        models.Preprint,
        pk=preprint_id,
        repository=request.repository,
    )
    review = get_object_or_404(
        models.Review,
        pk=review_id,
        preprint=preprint,
    )
    form = forms.ReviewDueDateForm(instance=review)

    if request.POST:
        fire_redirect = True
        if 'reset' in request.POST:
            review.reset(user=request.user)
            messages.add_message(request, messages.SUCCESS, 'Review reset.')
        if 'withdraw' in request.POST:
            reason = request.POST.get('withdraw_reason', 'No reason supplied.')
            review.withdraw(reason, request)
            messages.add_message(request, messages.SUCCESS, 'Review withdrawn')
        if 'accept' in request.POST:
            review.accept(request)
            messages.add_message(request, messages.SUCCESS, 'Marked as Accepted')
        if 'publish' in request.POST:
            review.publish(user=request.user)
            messages.add_message(request, messages.SUCCESS, 'Review comment published')
        if 'unpublish' in request.POST:
            review.unpublish(user=request.user)
            messages.add_message(request, messages.SUCCESS, 'Review comment unpublished')
        if 'edit' in request.POST:
            form = forms.ReviewDueDateForm(
                request.POST,
                instance=review,
            )
            if form.is_valid():
                form.save()
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    'Due Date updated.',
                )
            else:
                fire_redirect = False

        if fire_redirect:
            return redirect(
                reverse(
                    'repository_review_detail',
                    kwargs={
                        'preprint_id': preprint_id,
                        'review_id': review.pk,
                    }
                )
            )

    template = 'repository/review/review_detail.html'
    context = {
        'review': review,
        'preprint': preprint,
        'form': form,
    }
    return render(
        request,
        template,
        context,
    )


@is_repository_manager
def manage_review(request, preprint_id):
    """
    Allows an editor to create and edit a review.
    """
    preprint = get_object_or_404(
        models.Preprint,
        pk=preprint_id,
        repository=request.repository,
    )
    form = forms.ReviewForm(
        preprint=preprint,
        manager=request.user,
    )
    if request.POST:
        form = forms.ReviewForm(
            request.POST,
            preprint=preprint,
            manager=request.user,
        )
        if form.is_valid():
            review = form.save()
            messages.add_message(
                request,
                messages.SUCCESS,
                'Review saved.',
            )
            return redirect(
                reverse(
                    'repository_notify_reviewer',
                    kwargs={
                        'preprint_id': preprint.pk,
                        'review_id': review.pk,
                    },
                )
            )

    template = 'repository/review/manage_review.html'
    context = {
        'form': form,
        'preprint': preprint,
        'reviewers': request.repository.reviewer_accounts(),
    }
    return render(
        request,
        template,
        context,
    )


@is_repository_manager
def notify_reviewer(request, preprint_id, review_id):
    preprint = get_object_or_404(
        models.Preprint,
        pk=preprint_id,
        repository=request.repository,
    )
    review = get_object_or_404(
        models.Review,
        pk=review_id,
        preprint=preprint,
    )
    message = repository_logic.get_review_notification(request, preprint, review)
    if request.POST:
        message = request.POST.get('message')
        event_logic.Events.raise_event(
            event_logic.Events.ON_PREPRINT_REVIEW_NOTIFICATION,
            **{
                'request': request,
                'preprint': preprint,
                'review': review,
                'message': message,
                'skip': True if 'skip' in request.POST else False,
            }
        )
        messages.add_message(
            request,
            messages.SUCCESS,
            'Invited review notification sent.',
        )
        if 'skip' not in request.POST:
            review.notification_sent = True
            review.save()
        return redirect(
            reverse(
                'repository_list_reviews',
                kwargs={'preprint_id': preprint.pk},
            )
        )

    template = 'repository/review/notify_reviewer.html'
    context = {
        'preprint': preprint,
        'review': review,
        'message': message,
    }
    return render(
        request,
        template,
        context,
    )


def submit_review(request, review_id, access_code):
    """
    Allows a reviewer to submit their review.
    """
    # Fetch a review where review_id and access code match and the review is
    # currently new or accepted.
    review = get_object_or_404(
        models.Review,
        pk=review_id,
        access_code=access_code,
        status__in=['new', 'accepted']
    )
    form = forms.ReviewCommentForm(
        review=review,
    )
    if request.POST:
        fire_redirect = True
        if 'accept' in request.POST:
            review.accept(request)
        if 'decline' in request.POST:
            review.decline(request)
            messages.add_message(
                request,
                messages.INFO,
                'Thanks for letting us know you cannot add a review comment.',
            )
        else:
            form = forms.ReviewCommentForm(
                request.POST,
                review=review,
            )
            if form.is_valid():
                form.save()
                review.complete(request)
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    'Review saved. Thank you for your contribution',
                )
            else:
                fire_redirect = False

        if fire_redirect:
            if request.user.is_authenticated:
                return redirect(
                    reverse(
                        'repository_dashboard',
                    )
                )
            return redirect(
                reverse(
                    'website_index',
                )
            )
    template = 'repository/review/submit_review.html'
    context = {
        'review': review,
        'form': form,
    }
    return render(
        request,
        template,
        context,
    )


def download_review_file(request, review_id, access_code):
    """
    Returns the latest version file for a given preprint.
    """
    review = get_object_or_404(
        models.Review,
        pk=review_id,
        access_code=access_code,
        status__in=['new', 'accepted']
    )
    file = review.preprint.current_version.file
    return files.serve_any_file(
        request,
        file,
        path_parts=(file.path_parts(),)
    )


@is_repository_manager
def edit_review_comment(request, preprint_id, review_id):
    preprint = get_object_or_404(
        models.Preprint,
        pk=preprint_id,
        repository=request.repository,
    )
    review = get_object_or_404(
        models.Review,
        pk=review_id,
        preprint=preprint,
    )
    form = forms.ReviewCommentForm(
        review=review,
    )
    if request.POST:
        form = forms.ReviewCommentForm(
            request.POST,
            review=review,
        )
        if form.is_valid():
            form.save()
            messages.add_message(
                request,
                messages.SUCCESS,
                'Review comment saved.',
            )
            return redirect(
                reverse(
                    'repository_review_detail',
                    kwargs={
                        'preprint_id': preprint.pk,
                        'review_id': review.pk,
                    }
                )
            )
    template = 'repository/review/edit_review_comment.html'
    context = {
        'preprint': preprint,
        'review': review,
        'form': form,
    }
    return render(
        request,
        template,
        context,
    )


@is_repository_manager
def manage_reviewers(request):
    role = core_models.Role.objects.get(slug='reviewer')
    user_search = []
    first_name = request.GET.get('first_name', '')
    last_name = request.GET.get('last_name', '')
    email = request.GET.get('email', '')

    if first_name or last_name or email:
        filters = {}
        if first_name and len(first_name) >= 2:
            filters['first_name__icontains'] = first_name
        if last_name and len(last_name) >= 2:
            filters['last_name__icontains'] = last_name
        if email and len(email) >= 2:
            filters['email__icontains'] = email

        user_search = core_models.Account.objects.filter(
            **filters, is_active=True,
        ).exclude(
            pk__in=request.repository.reviewer_accounts().values("id"),
        )

    if request.POST and ('add_reviewer' in request.POST or 'remove_reviewer' in request.POST):
        if 'add_reviewer' in request.POST:
            account_id = request.POST.get('add_reviewer')
            account = get_object_or_404(
                core_models.Account,
                pk=account_id,
                is_active=True,
            )
            role, created = models.RepositoryRole.objects.get_or_create(
                repository=request.repository,
                user=account,
                role=role,
            )
            messages.add_message(
                request,
                messages.SUCCESS,
                '{} now has the Reviewer role.'.format(
                    account.full_name(),
                )
            )
        if 'remove_reviewer' in request.POST:
            account_id = request.POST.get('remove_reviewer')
            account = get_object_or_404(
                core_models.Account,
                pk=account_id,
                is_active=True,
            )
            roles = models.RepositoryRole.objects.filter(
                repository=request.repository,
                user=account,
                role=role,
            ).delete()
            messages.add_message(
                request,
                messages.SUCCESS,
                '{} no longer has the reviewer role.'.format(
                    account.full_name(),
                )
            )
        return redirect(
            reverse(
                'repository_manage_reviewers',
            )
        )

    template = 'repository/review/manage_reviewers.html'
    context = {
        'reviewers': request.repository.reviewer_accounts(),
        'user_search': user_search,
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
    }
    return render(
        request,
        template,
        context,
    )


@is_repository_manager
def repository_licenses(request):
    """
    Allows a repository manage to select the active licenses from the Press set.
    """
    form = forms.ActiveLicenseForm(
        instance=request.repository,
    )
    if request.POST:
        form = forms.ActiveLicenseForm(
            request.POST,
            instance=request.repository,
        )
        if form.is_valid():
            form.save()
            messages.add_message(
                request,
                messages.SUCCESS,
                'Active Licenses Saved.'
            )
            return redirect(
                reverse(
                    'repository_licenses',
                )
            )
    template = 'admin/repository/licenses.html'
    context = {
        'form': form,
    }
    return render(
        request,
        template,
        context,
    )


@is_repository_manager
def send_user_email(request, user_id, preprint_id):
    user = get_object_or_404(core_models.Account, pk=user_id)
    form = core_forms.EmailForm(
        initial={'body': '<br/ >{signature}'.format(
            signature=request.user.signature)},
    )
    close, article, preprint = False, None, None
    preprint = get_object_or_404(
        models.Preprint,
        pk=preprint_id,
        repository=request.repository,
    )

    if request.POST and 'send' in request.POST:
        form = core_forms.EmailForm(request.POST)

        if form.is_valid():
            core_logic.send_email(
                user,
                form,
                request,
                article,
                preprint,
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
