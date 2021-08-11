__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django.contrib import messages
from django.urls import reverse
from django.db.models import Q
from django.http import Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from copyediting import models, logic, forms
from core import models as core_models, files
from events import logic as event_logic
from security.decorators import (
    production_user_or_editor_required, copyeditor_user_required,
    copyeditor_for_copyedit_required, article_author_required,
    editor_user_required, senior_editor_user_required
)

from submission import models as submission_models


@senior_editor_user_required
def copyediting(request):
    """
    View shows the user a list of articles in Copyediting
    :param request: django request object
    :return: a contextualised template
    """

    articles_in_copyediting = submission_models.Article.objects.filter(stage__in=submission_models.COPYEDITING_STAGES,
                                                                       journal=request.journal)

    template = 'copyediting/copyediting.html'
    context = {
        'articles_in_copyediting': articles_in_copyediting,
    }

    return render(request, template, context)


@editor_user_required
def article_copyediting(request, article_id):
    """
    View allows Editor to view and assign copyeditors and author reviews.
    :param request: django request object
    :param article_id: PK of an Article
    :return: a contextualised template
    """

    article = get_object_or_404(submission_models.Article, pk=article_id)
    copyeditor_assignments = models.CopyeditAssignment.objects.filter(
        article=article,
    )

    message_kwargs = {'request': request, 'article': article}

    if 'delete' in request.POST:
        assignment_id = request.POST.get('delete')
        assignment = get_object_or_404(models.CopyeditAssignment,
                                       article=article,
                                       pk=assignment_id,
                                       decision__isnull=True)
        message_kwargs['copyedit_assignment'] = assignment
        messages.add_message(
            request,
            messages.SUCCESS,
            'Assignment #{0} delete'.format(assignment_id),
        )
        event_logic.Events.raise_event(
            event_logic.Events.ON_COPYEDIT_DELETED,
            **message_kwargs,
        )
        assignment.delete()
        return redirect(
            reverse('article_copyediting', kwargs={'article_id': article.pk})
        )

    if request.POST and 'complete' in request.POST:
        event_logic.Events.raise_event(
            event_logic.Events.ON_COPYEDIT_COMPLETE,
            task_object=article,
            **message_kwargs,
        )
        workflow_kwargs = {
            'handshake_url': 'copyediting',
            'request': request,
            'article': article,
            'switch_stage': True,
        }
        return event_logic.Events.raise_event(
            event_logic.Events.ON_WORKFLOW_ELEMENT_COMPLETE,
            task_object=article,
            **workflow_kwargs,
        )

    template = 'copyediting/article_copyediting.html'
    context = {
        'article': article,
        'copyeditor_assignments': copyeditor_assignments,
        'in_copyediting': True if article.stage in submission_models.COPYEDITING_STAGES else False,
    }

    return render(request, template, context)


@editor_user_required
def add_copyeditor_assignment(request, article_id):
    """
    Allows a production or editor user to add a new copyeditingassignment.
    :param request: HttpRequest object
    :param article_id: a submission.models.Article PK
    :return: HttpRequest object
    """
    article = get_object_or_404(submission_models.Article, pk=article_id)
    copyeditors = logic.get_copyeditors(article)
    copyeditor_pks = [copyeditor.user.pk for copyeditor in copyeditors]
    files = article.manuscript_files.all() | article.data_figure_files.all()

    form = forms.CopyeditAssignmentForm(
        copyeditor_pks=copyeditor_pks,
        files=files,
    )

    if request.POST:
        form = forms.CopyeditAssignmentForm(
            request.POST,
            copyeditor_pks=copyeditor_pks,
            files=files,
        )

        if form.is_valid():
            copyedit = form.save(
                editor=request.user,
                article=article,
            )

            return redirect(
                reverse(
                    'notify_copyeditor_assignment',
                    kwargs={
                        'article_id': article.pk,
                        'copyedit_id': copyedit.pk,
                    }
                )
            )

    template = 'copyediting/add_copyeditor_assignment.html'
    context = {
        'article': article,
        'copyeditors': copyeditors,
        'form': form,
    }

    return render(request, template, context)


@editor_user_required
def notify_copyeditor_assignment(request, article_id, copyedit_id):
    """
    Allows a production or editor user to send an email to a newly assigned copyeditor.
    :param request: HttpRequest object
    :param article_id: a submission.models.Article PK
    :param copyedit_id: a CopyeditAssignment PK
    :return: HttpRequest object
    """
    article = get_object_or_404(submission_models.Article, pk=article_id)
    copyedit = get_object_or_404(models.CopyeditAssignment, pk=copyedit_id)
    user_message_content = logic.get_copyeditor_notification(request, article, copyedit)

    if request.POST:
        user_message_content = request.POST.get('content_email')

        kwargs = {
            'user_message_content': user_message_content,
            'article': article,
            'copyedit_assignment': copyedit,
            'request': request,
            'skip': True if 'skip' in request.POST else False
        }

        event_logic.Events.raise_event(event_logic.Events.ON_COPYEDIT_ASSIGNMENT, **kwargs)
        messages.add_message(request, messages.INFO, 'Copyedit requested.')
        return redirect(reverse('article_copyediting', kwargs={'article_id': article.pk}))

    template = 'copyediting/notify_copyeditor_assignment.html'
    context = {
        'article': article,
        'copyedit': copyedit,
        'user_message_content': user_message_content,
    }

    return render(request, template, context)


@editor_user_required
def edit_assignment(request, article_id, copyedit_id):
    """
    Allows a production or editor user to make changes to an existing CopyeditAssignment
    :param request: HttpRequest object
    :param article_id:  a submission.models.Article PK
    :param copyedit_id: a CopyeditAssignment PK
    :return:
    """
    article = get_object_or_404(submission_models.Article, pk=article_id)
    copyedit = get_object_or_404(models.CopyeditAssignment, pk=copyedit_id)

    if copyedit.decision:
        messages.add_message(
            request,
            messages.WARNING,
            'This task is underway so cannot be edited.'
        )
        return redirect(
            reverse(
                'article_copyediting',
                kwargs={'article_id': article.pk},
            )
        )

    form = forms.CopyeditAssignmentForm(
        instance=copyedit,
    )

    if request.POST:
        form = forms.CopyeditAssignmentForm(request.POST, instance=copyedit)

        if form.is_valid():
            form.save()
            kwargs = {'copyedit_assignment': copyedit, 'request': request,
                      'skip': True if 'skip' in request.POST else False}
            event_logic.Events.raise_event(
                event_logic.Events.ON_COPYEDIT_UPDATED,
                **kwargs
            )
            messages.add_message(
                request,
                messages.SUCCESS,
                'Copyedit assignment updated.',
            )
            return redirect(
                reverse(
                    'article_copyediting',
                    kwargs={'article_id': article.pk},
                )
            )

    template = 'copyediting/edit_assignment.html'
    context = {
        'article': article,
        'copyedit': copyedit,
        'form': form,
    }

    return render(request, template, context)


@copyeditor_user_required
def copyedit_requests(request):
    """
    Displays a list of new, in progress and complete copyediting requests to a user with copyediting role.
    :param request: HttpRequest object
    :return: HttpResponse object
    """
    new_requests = models.CopyeditAssignment.objects.filter(
        copyeditor=request.user,
        decision__isnull=True,
        article__journal=request.journal
    )

    active_requests = models.CopyeditAssignment.objects.filter(
        (Q(copyeditor=request.user) &
         Q(decision='accept') &
         Q(copyedit_reopened__isnull=True) &
         Q(copyeditor_completed__isnull=True)),
        article__journal=request.journal
    )

    reopened_requests = models.CopyeditAssignment.objects.filter(
        copyeditor=request.user,
        copyeditor_completed__isnull=False,
        copyedit_reopened__isnull=False,
        copyedit_reopened_complete__isnull=True,
        copyedit_accepted__isnull=True,
        article__journal=request.journal,
    )

    completed_requests = models.CopyeditAssignment.objects.filter(
        Q(copyeditor=request.user,
          decision='accept',
          copyedit_accepted__isnull=False) |
        Q(copyeditor=request.user,
          copyeditor_completed__isnull=False),
        article__journal=request.journal
    )

    template = 'copyediting/copyedit_requests.html'
    context = {
        'new_requests': new_requests,
        'active_requests': active_requests,
        'reopened_requests': reopened_requests,
        'completed_requests': completed_requests,
    }

    return render(request, template, context)


@copyeditor_user_required
def copyedit_request_decision(request, copyedit_id, decision):
    """
    Records a user's decision on whether they will do a copyedit.
    :param request: HttpRequest object
    :param copyedit_id: a CopyeditAssignment PK
    :param decision: a string, either 'accept' or 'decline'
    :return: HttpResponse object
    """
    copyedit = get_object_or_404(models.CopyeditAssignment, pk=copyedit_id)

    if decision == 'accept':
        copyedit.decision = 'accept'
        copyedit.date_decided = timezone.now()
        messages.add_message(request, messages.INFO, 'Copyediting request {0} accepted'.format(copyedit.pk))
    elif decision == 'decline':
        copyedit.decision = 'decline'
        copyedit.date_decided = timezone.now()
        messages.add_message(request, messages.INFO, 'Copyediting request {0} declined'.format(copyedit.pk))
    else:
        messages.add_message(request, messages.WARNING, 'Decision must be "accept" or "decline".')

    kwargs = {
        'copyedit_assignment': copyedit,
        'decision': decision,
        'request': request,
    }
    event_logic.Events.raise_event(event_logic.Events.ON_COPYEDITOR_DECISION, **kwargs)

    copyedit.save()
    return redirect(reverse('copyedit_requests'))


@copyeditor_for_copyedit_required
def do_copyedit(request, copyedit_id):
    """
    Displays the form for completing a copyedit assignment, only if the decision is accept and it has not previously
    been completed.
    :param request: HttpRequest object
    :param copyedit_id: a CopyeditAssignment PK
    :return: HttpResponse object
    """
    copyedit = get_object_or_404(models.CopyeditAssignment,
                                 Q(copyeditor_completed__isnull=True) | Q(copyedit_reopened__isnull=False),
                                 copyedit_reopened_complete__isnull=True,
                                 pk=copyedit_id,
                                 decision='accept')
    form = forms.CopyEditForm(instance=copyedit)

    if request.POST:
        form = forms.CopyEditForm(request.POST, instance=copyedit)

        if not copyedit.copyeditor_files.all():
            form.add_error(None, 'You must upload a file before you can complete your copyediting task.')

        if form.is_valid():
            copyedit = form.save()

            if copyedit.copyedit_reopened:
                copyedit.copyedit_reopened_complete = timezone.now()
            else:
                copyedit.copyeditor_completed = timezone.now()
            copyedit.save()
            messages.add_message(request, messages.SUCCESS, 'Initial copyedit assignment completed.')

            kwargs = {
                'article': copyedit.article,
                'copyedit_assignment': copyedit,
                'request': request,
            }

            event_logic.Events.raise_event(event_logic.Events.ON_COPYEDIT_ASSIGNMENT_COMPLETE, **kwargs)
            return redirect(reverse('copyedit_requests'))

    template = 'copyediting/do_copyedit.html'
    context = {
        'copyedit': copyedit,
        'form': form,
    }

    return render(request, template, context)


@copyeditor_for_copyedit_required
def do_copyedit_add_file(request, copyedit_id):
    """
    Allows a copyeditor to upload a new file and associate it with the article, only if the assignment is not complete.
    :param request: HttpRequest
    :param copyedit_id: a CopyeditAssignment PK
    :return: HttpResponse object
    """
    copyedit = get_object_or_404(models.CopyeditAssignment,
                                 Q(copyeditor_completed__isnull=True) | Q(copyedit_reopened__isnull=False),
                                 copyedit_reopened_complete__isnull=True,
                                 pk=copyedit_id,
                                 decision='accept')
    errors = None
    if request.POST:
        errors = logic.handle_file_post(request, copyedit)

        if not errors:
            return redirect(reverse('do_copyedit', kwargs={'copyedit_id': copyedit.id}))

    template = 'copyediting/upload_file.html'
    context = {
        'copyedit': copyedit,
        'errors': errors,
    }

    return render(request, template, context)


@copyeditor_for_copyedit_required
def copyeditor_file(request, copyedit_id, file_id):
    """ Serves an article file.
    :param request: the request associated with this call
    :param copyedit_id: the CopyeditAssignment id.
    :param file_id: the file ID to serve
    :return: a streaming response of the requested file or 404
    """
    copyedit_assignment = models.CopyeditAssignment.objects.get(
        Q(copyeditor_completed__isnull=True) | Q(copyedit_reopened__isnull=False),
        copyedit_reopened_complete__isnull=True,
        pk=copyedit_id,
        decision='accept')
    article_object = copyedit_assignment.article

    file_object = core_models.File.objects.get(pk=file_id)

    if not file_object:
        raise Http404()

    return files.serve_file(request, file_object, article_object)


@editor_user_required
def editor_review(request, article_id, copyedit_id):
    """
    Allows Editor to review a copyedit.
    :param request: Django request object
    :param article_id: Article PK
    :param copyedit_id: CopyeditAssignment PK
    :return: Contextualised Django template
    """
    article = get_object_or_404(
        submission_models.Article,
        pk=article_id,
        journal=request.journal,
    )
    copyedit = get_object_or_404(models.CopyeditAssignment, pk=copyedit_id)

    if request.POST:
        if 'accept_note' in request.POST:
            logic.accept_copyedit(copyedit, article, request)
        elif 'author_review' in request.POST:
            author_review = models.AuthorReview.objects.create(
                author=article.correspondence_author,
                assignment=copyedit,
                notified=True
            )
            return redirect(
                reverse(
                    'request_author_copyedit',
                    kwargs={
                        'article_id': article.pk,
                        'copyedit_id': copyedit.pk,
                        'author_review_id': author_review.pk,
                    }
                )
            )
        elif 'reset_note' in request.POST:
            logic.reset_copyedit(copyedit, article, request)

        return redirect(reverse('article_copyediting', kwargs={'article_id': article.id}))

    if request.GET.get('file_id'):
        return logic.attempt_to_serve_file(request, copyedit)

    template = 'copyediting/editor_review.html'
    context = {
        'article': article,
        'copyedit': copyedit,
        'accept_message': logic.get_copyedit_message(request, article, copyedit, 'copyeditor_ack'),
        'reopen_message': logic.get_copyedit_message(request, article, copyedit, 'copyeditor_reopen_task'),
    }

    return render(request, template, context)


@editor_user_required
def request_author_copyedit(request, article_id, copyedit_id,
                            author_review_id):
    """
    Allows an editor to request an Author undertake a review.
    :param request:
    :param article_id:
    :param copyedit_id:
    :param author_review_id:
    :return:
    """
    article = get_object_or_404(
        submission_models.Article,
        pk=article_id,
        journal=request.journal,
    )
    copyedit = get_object_or_404(
        models.CopyeditAssignment,
        pk=copyedit_id,
        article=article,
    )
    author_review = get_object_or_404(
        models.AuthorReview,
        pk=author_review_id,
        assignment=copyedit,
    )

    email_content = logic.get_copyedit_message(
        request,
        article,
        copyedit,
        'copyeditor_notify_author',
        author_review=author_review,

    )

    email_subject = request.journal.get_setting(
        'email_subject',
        'subject_copyeditor_notify_author',
    )

    if request.POST:
        logic.request_author_review(
            request,
            article,
            copyedit,
            author_review,
        )

        messages.add_message(
            request,
            messages.SUCCESS,
            'Author review requested.',
        )

        return redirect(
            reverse(
                'editor_review',
                kwargs={
                    'article_id': article.pk,
                    'copyedit_id': copyedit.pk,
                }
            )
        )

    template = 'copyediting/request_author_copyedit.html'
    context = {
        'article': article,
        'copyedit': copyedit,
        'author_review': author_review,
        'email_content': email_content,
        'email_subject': email_subject,
    }

    return render(request, template, context)


@article_author_required
def author_copyedit(request, article_id, author_review_id):
    """
    Allows an author to review a copyedit.
    :param request: django request object
    :param article_id: Article PK
    :param author_review_id: AuthorReview pk
    :return: contextualised template
    """
    author_review = get_object_or_404(models.AuthorReview,
                                      pk=author_review_id,
                                      assignment__article__id=article_id,
                                      date_decided__isnull=True)
    copyedit = author_review.assignment
    form = forms.AuthorCopyeditForm(instance=author_review)

    if request.POST:
        form = forms.AuthorCopyeditForm(request.POST, instance=author_review)

        if form.is_valid():
            author_review = form.save(commit=False)
            author_review.date_decided = timezone.now()
            author_review.save()

            kwargs = {'author_review': author_review, 'copyedit': copyedit, 'request': request}
            event_logic.Events.raise_event(event_logic.Events.ON_COPYEDIT_AUTHOR_REVIEW_COMPLETE, **kwargs)

            return redirect(reverse('core_dashboard'))

    if request.GET.get('file_id'):
        return logic.attempt_to_serve_file(request, copyedit)

    template = 'copyediting/author_review.html'
    context = {
        'author_review': author_review,
        'copyedit': copyedit,
        'form': form,
    }

    return render(request, template, context)


@article_author_required
def author_update_file(request, article_id, author_review_id, file_id):
    """
    Allows an article's author to update a copyeditor_file
    :param request: django request object
    :param article_id: Article pk
    :param author_review_id: AuthorReview pk
    :param file_id: File pk
    :return: contextualised django template
    """
    author_review = get_object_or_404(models.AuthorReview,
                                      pk=author_review_id,
                                      assignment__article__id=article_id,
                                      date_decided__isnull=True)
    copyedit = author_review.assignment

    try:
        file = copyedit.copyeditor_files.get(pk=file_id)
    except core_models.File.DoesNotExist:
        raise Http404

    if request.POST and request.FILES:

        if 'replacement' in request.POST:
            uploaded_file = request.FILES.get('replacement-file')
            label = request.POST.get('label')
            new_file = files.save_file_to_article(uploaded_file, copyedit.article, request.user,
                                                  replace=file, is_galley=False, label=label)
            files.replace_file(copyedit.article, file, new_file, copyedit=copyedit, retain_old_label=False)
            author_review.files_updated.add(new_file)

        return redirect(reverse('author_copyedit',
                                kwargs={'article_id': article_id, 'author_review_id': author_review.pk}))

    if request.GET.get('file_id'):
        return logic.attempt_to_serve_file(request, copyedit)

    template = 'copyediting/author_update_file.html'
    context = {
        'author_review': author_review,
        'copyedit': copyedit,
        'file': file,
    }

    return render(request, template, context)
