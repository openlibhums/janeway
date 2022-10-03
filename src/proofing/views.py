__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import json

from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import HttpResponse
from django.db.models import Q

from proofing import models as proofing_models
from security.decorators import (
    proofing_manager_or_editor_required, proofing_manager_for_article_required,
    typesetter_user_required, proofreader_for_article_required,
    typesetter_for_corrections_required, proofing_manager_roles,
)
from submission import models as submission_models
from core import models as core_models, files
from proofing import models, logic, forms
from events import logic as event_logic
from journal import models as journal_models
from journal.views import article_figure


@proofing_manager_roles
def proofing_list(request):
    """
    Displays lists of articles and proofing assignments
    :param request: HttpRequest object
    :return: HttpResponse object
    """
    assigned_table = proofing_models.ProofingAssignment.objects.all()
    my_table = proofing_models.ProofingAssignment.objects.values_list('article_id', flat=True).filter(
        proofing_manager=request.user)

    assigned = [assignment.article.pk for assignment in assigned_table]
    unassigned_articles = submission_models.Article.objects.filter(stage=submission_models.STAGE_PROOFING,
                                                                   journal=request.journal).exclude(
        id__in=assigned)
    assigned_articles = submission_models.Article.objects.filter(stage=submission_models.STAGE_PROOFING,
                                                                 journal=request.journal).exclude(
        id__in=unassigned_articles)

    my_articles = submission_models.Article.objects.filter(stage=submission_models.STAGE_PROOFING,
                                                           journal=request.journal,
                                                           id__in=my_table)

    template = 'proofing/index.html'
    context = {
        'proofing_articles': unassigned_articles,
        'assigned_articles': assigned_articles,
        'my_articles': my_articles,
        'production_managers': core_models.AccountRole.objects.filter(role__slug='proofing-manager')
    }

    return render(request, template, context)


@proofing_manager_or_editor_required
def proofing_assign_article(request, article_id, user_id=None):
    """
    Assigns a Proofing Manager with a task
    :param request: HttpRequest object
    :param article_id: Article object PK
    :param user_id: Account object PK
    :return: HttpRedirect
    """
    article = get_object_or_404(submission_models.Article, pk=article_id, journal=request.journal)
    user = get_object_or_404(core_models.Account, pk=user_id)

    if user.is_proofing_manager:
        proofing_assignment = models.ProofingAssignment.objects.create(article=article,
                                                                       proofing_manager=user,
                                                                       notified=True,
                                                                       editor=request.user)
        proofing_assignment.add_new_proofing_round()

        message = "{0} has been assigned as proofing manager to {1}".format(
            proofing_assignment.proofing_manager.full_name(),
            proofing_assignment.article.title)
        messages.add_message(request, messages.INFO, message)

        kwargs = {
            'request': request, 'proofing_assignment': proofing_assignment,
        }
        event_logic.Events.raise_event(event_logic.Events.ON_PROOFING_MANAGER_ASSIGNMENT, task_object=article, **kwargs)

    else:
        messages.add_message(request, messages.WARNING, 'User is not a proofing manager.')

    return redirect(reverse('proofing_list'))


@proofing_manager_or_editor_required
def proofing_unassign_article(request, article_id):
    """
    Unassigns a proofing manager assignment
    :param request: HttpRequest object
    :param article_id: Article object PK
    :return: HttpRedirect
    """
    article = submission_models.Article.objects.get(id=article_id, journal=request.journal)

    if not article.proofingassignment.current_proofing_round().proofingtask_set.all():
        article.proofingassignment.delete()
    else:
        messages.add_message(request, messages.WARNING, 'This assignment has active tasks, cannot be deleted.')

    return redirect('proofing_list')


@proofing_manager_for_article_required
def proofing_article(request, article_id):
    """
    Displays the proofing control page, allows PM to add tasks, edit galleys and mark proofing as complete
    :param request: HttpRequest object
    :param article_id: Article object PK
    :return: HttpRedirect if POST or HttpResponse
    """
    article = get_object_or_404(
        submission_models.Article.objects.select_related(
            'productionassignment'
        ),
        pk=article_id,
        journal=request.journal,
    )
    current_round = article.proofingassignment.current_proofing_round()
    proofreaders = logic.get_all_possible_proofers(
        journal=request.journal,
        article=article,
    )
    form = forms.AssignProofreader()
    modal = None

    if request.POST:

        if 'new-round' in request.POST:
            logic.handle_closing_active_task(request, article)
            new_round = article.proofingassignment.add_new_proofing_round()
            messages.add_message(
                request,
                messages.SUCCESS,
                'New round {0} added.'.format(new_round.number),
            )
            return redirect(
                reverse(
                    'proofing_article',
                    kwargs={'article_id': article.pk},
                )
            )

        if 'new-proofreader' in request.POST:

            if not current_round.can_add_another_proofreader(request.journal):
                messages.add_message(
                    request,
                    messages.WARNING,
                    'The number of proofreaders per round has been limited.'
                    ' You cannot add another proofreader in this round.',
                )
                return redirect(
                    reverse(
                        'proofing_article',
                        kwargs={'article_id': article.pk},
                    )
                )

            form = forms.AssignProofreader(request.POST)
            user = logic.get_user_from_post(request, article)
            galleys = logic.get_galleys_from_post(request)

            if not user:
                form.add_error(None, 'You must select a user.')

            if not galleys:
                form.add_error(None, 'You must select at least one Galley.')

            if form.is_valid():
                proofing_task = form.save(commit=False)
                proofing_task.proofreader = user
                proofing_task.round = current_round
                proofing_task.save()
                proofing_task.galleys_for_proofing.add(*galleys)
                return redirect(
                    reverse(
                        'notify_proofreader',
                        kwargs={
                            'article_id': article.pk,
                            'proofing_task_id': proofing_task.pk,
                        }
                    )
                )

            # Set the modal to open if this page is not redirected.
            modal = 'add_proofer'

    template = 'proofing/proofing_article.html'
    context = {
        'article': article,
        'proofreaders': proofreaders,
        'form': form,
        'modal': modal,
        'user': user if request.POST else None,
        'galleys': galleys if request.POST else None
    }

    return render(request, template, context)


@proofing_manager_for_article_required
def delete_proofing_round(request, article_id, round_id):
    """
    Presents an interface for a PM to delete a proofing round.
    :param request: HttpRequest object
    :param article_id: Article object PK
    :param round_id: Round object PK
    :return: HttpResponse or HttpRedirect
    """
    article = get_object_or_404(
        submission_models.Article,
        pk=article_id,
        journal=request.journal,
    )

    round = get_object_or_404(
        models.ProofingRound,
        pk=round_id,
        assignment__article=article,
    )

    proofing_tasks = models.ProofingTask.objects.filter(
        round=round,
    )

    correction_tasks = models.TypesetterProofingTask.objects.filter(
        proofing_task__in=proofing_tasks,
    )

    if request.POST:
        round.delete_round_relations(
            request,
            article,
            proofing_tasks,
            correction_tasks,
        )
        logic.delete_round(article, round)
        messages.add_message(
            request,
            messages.INFO,
            'Proofing Round Deleted',
        )
        return redirect(
            reverse(
                'proofing_article',
                kwargs={'article_id': article.pk}
            )
        )

    template = 'proofing/delete_proofing_round.html'
    context = {
        'article': article,
        'round': round,
        'proofing_tasks': proofing_tasks,
        'correction_tasks': correction_tasks,
    }

    return render(request, template, context)


@proofing_manager_for_article_required
def edit_proofing_assignment(request, article_id, proofing_task_id):
    """
    Allows a PM to edit an existing ProofingTask
    :param request: HttpRequest object
    :param article_id: Article object PK
    :param proofing_task_id: ProofingTask PK
    :return: HttpRedirect or HttpResponse
    """
    article = get_object_or_404(submission_models.Article,
                                pk=article_id,
                                journal=request.journal)
    proofing_task = get_object_or_404(models.ProofingTask,
                                      pk=proofing_task_id)

    form = forms.AssignProofreader(instance=proofing_task)

    if request.POST:

        if 'delete' in request.POST:
            kwargs = {'article': article,
                      'proofing_task': proofing_task,
                      'request': request}
            event_logic.Events.raise_event(
                event_logic.Events.ON_CANCEL_PROOFING_TASK,
                task_object=article,
                **kwargs,
            )
            proofing_task.delete()
            messages.add_message(
                request,
                messages.SUCCESS,
                'Proofing task deleted.',
            )

            return redirect(
                reverse(
                    'proofing_article',
                    kwargs={'article_id': article.id},
                )
            )

        if 'reset' in request.POST:
            proofing_task.reset()
            logic.add_reset_log_entry(
                request,
                proofing_task,
                article,
            )
            messages.add_message(
                request,
                messages.INFO,
                'Proofing task reset.',
            )
            return redirect(
                reverse(
                    'proofing_article',
                    kwargs={'article_id': article.id},
                )
            )

        form = forms.AssignProofreader(
            request.POST,
            instance=proofing_task,
        )
        galleys = logic.get_galleys_from_post(request)

        if not galleys:
            form.add_error(None, 'You must select at least one Galley.')

        if form.is_valid():
            proofing_task = form.save()
            proofing_task.save()

            for galley in proofing_task.galleys_for_proofing.all():
                if galley not in galleys:
                    proofing_task.galleys_for_proofing.remove(galley)
            proofing_task.galleys_for_proofing.add(*galleys)

            kwargs = {
                'article': article,
                'proofing_task': proofing_task,
                'request': request
            }
            event_logic.Events.raise_event(
                event_logic.Events.ON_EDIT_PROOFING_TASK,
                task_object=article,
                **kwargs,
            )

            return redirect(reverse('proofing_article', kwargs={'article_id': article.id}))

    template = 'proofing/edit_proofing_assignment.html'
    context = {
        'article': article,
        'proofing_task': proofing_task,
        'form': form,
        'galleys': proofing_task.galleys_for_proofing.all(),
    }

    return render(request, template, context)


@proofing_manager_for_article_required
def notify_proofreader(request, article_id, proofing_task_id):
    """
    Optionally, a PM can notify an proofreader of their assignment.
    :param request: HttpRequest object
    :param article_id: Article object PK
    :param proofing_task_id: ProofingTask PK
    :return: HttpRedirect or HttpResponse
    """
    article = get_object_or_404(submission_models.Article.objects.select_related('productionassignment'), pk=article_id)
    proofing_task = get_object_or_404(models.ProofingTask, pk=proofing_task_id)
    user_message_content = logic.get_notify_proofreader(request, article, proofing_task)

    if request.POST:
        kwargs = {
            'request': request,
            'user_content_message': request.POST.get('content_email'),
            'article': article,
            'proofing_task': proofing_task,
            'skip': True if 'skip' in request.POST else False
        }
        event_logic.Events.raise_event(event_logic.Events.ON_NOTIFY_PROOFREADER,
                                       task_object=article,
                                       **kwargs)
        return redirect(reverse('proofing_article', kwargs={'article_id': article.id}))

    template = 'proofing/notify_proofreader.html'
    context = {
        'article': article,
        'proofing_task': proofing_task,
        'user_message_content': user_message_content
    }

    return render(request, template, context)


@login_required
def proofing_requests(request, proofing_task_id=None, decision=None):
    """
    Displays proofing request to proofreaders
    :param request: HttpRequest object
    :param proofing_task_id: ProofingTask PK
    :param decision: string,
    :return: HttpResponse or HttpRedirect
    """
    if proofing_task_id:

        if proofing_task_id:
            logic.handle_proof_decision(request, proofing_task_id, decision)

        return redirect(reverse('proofing_requests'))

    new, active, completed = logic.get_tasks(request)

    template = 'proofing/proofing_requests.html'
    context = {
        'new_requests': new,
        'active_requests': active,
        'completed_requests': completed,

    }

    return render(request, template, context)


@typesetter_user_required
def correction_requests(request):

    if request.POST:
        typeset_task_id = request.POST.get('typeset_task_id', None)
        decision = request.POST.get('decision', None)

        if typeset_task_id and decision:
            logic.handle_typeset_decision(request, typeset_task_id, decision)
        else:
            messages.add_message(
                request,
                messages.WARNING,
                'Task ID or Decision missing.'
            )

        return redirect(reverse('proofing_correction_requests'))

    new, active, completed = logic.get_typesetting_tasks(request)

    template = 'proofing/correction_requests.html'
    context = {
        'new_typesetting_requests': new,
        'active_typesetting_requests': active,
        'completed_typesetting_requests': completed,
    }

    return render(request, template, context)


@proofreader_for_article_required
def do_proofing(request, proofing_task_id, article_id=None):
    """
    Allows a proofreader to undertake a proofingtask
    :param request: HttpRequest object
    :param proofing_task_id: ProofingTask object PK
    :param article_id: Article object PK
    :return: HttpResponse object
    """
    modal = None

    if not article_id:
        proofing_task = get_object_or_404(
            models.ProofingTask.active_objects,
            pk=proofing_task_id,
            completed__isnull=True,
        )
        proofing_manager = False
    else:
        proofing_task = get_object_or_404(
            models.ProofingTask.active_objects,
            pk=proofing_task_id,
            completed__isnull=False,
        )
        proofing_manager = True

    article = proofing_task.round.assignment.article

    if request.POST and 'complete' in request.POST:
        proofing_task.completed = timezone.now()
        proofing_task.save()
        kwargs = {'proofing_task': proofing_task, 'article': article, 'request': request}
        event_logic.Events.raise_event(event_logic.Events.ON_COMPLETE_PROOFING_TASK,
                                       task_object=article,
                                       **kwargs)
        return redirect(reverse('proofing_requests'))

    elif request.POST and 'upload' in request.POST:
        modal = logic.handle_annotated_galley_upload(request, proofing_task, article)

    template = 'proofing/do_proofing.html'
    context = {
        'proofing_task': proofing_task,
        'article': article,
        'proofing_manager': proofing_manager,
        'modal': modal
    }

    return render(request, template, context)


@proofreader_for_article_required
def preview_galley(request, proofing_task_id, galley_id):
    """
    Displays a preview of a galley object
    :param request: HttpRequest object
    :param proofing_task_id: ProofingTask object PK
    :param galley_id: Galley object PK
    :return: HttpResponse
    """
    proofing_task = get_object_or_404(models.ProofingTask, pk=proofing_task_id)
    galley = get_object_or_404(proofing_task.galleys_for_proofing, pk=galley_id)

    article_content = ""
    if galley.type == 'xml' or galley.type == 'html':
        template = 'proofing/preview/rendered.html'
        try:
            article_content = galley.file_content()
        except Exception as e:
            messages.add_message(
                request,
                messages.ERROR,
                'Errors found rendering this galley',
            )
    elif galley.type == 'epub':
        template = 'proofing/preview/epub.html'
    else:
        template = 'proofing/preview/embedded.html'

    context = {
        'proofing_task': proofing_task,
        'galley': galley,
        'article': proofing_task.round.assignment.article,
        'article_content': article_content,
    }

    return render(request, template, context)


@proofing_manager_for_article_required
def request_typesetting_changes(request, article_id, proofing_task_id):
    """
    Allows a PM to request typesetters make changes to an article's Galleys.
    :param request: HttpRequest object
    :param article_id: Article object PK
    :param proofing_task_id: ProofingTask PK
    :return: HttpResponse
    """
    article = get_object_or_404(submission_models.Article, pk=article_id)
    proofing_task = get_object_or_404(models.ProofingTask, pk=proofing_task_id)
    form = forms.AssignTypesetter()
    comments = proofing_task.review_comments()

    if request.POST:
        form = forms.AssignTypesetter(request.POST)
        user = logic.get_user_from_post(request, article, True)
        galleys = logic.get_galleys_from_post(request)
        files = logic.get_files_from_post(request)

        if not user:
            form.add_error(None, 'You must select a typesetter.')

        if not galleys:
            form.add_error(None, 'You must select at least one galley.')

        if form.is_valid():
            typeset_task = form.save(
                proofing_task,
                user,
                comments,
                commit=True,
            )
            typeset_task.galleys.add(*galleys)
            typeset_task.files.add(*files)

            return redirect(
                reverse(
                    'notify_typesetter_changes',
                    kwargs={'article_id': article.pk,
                            'proofing_task_id': proofing_task.pk,
                            'typeset_task_id': typeset_task.pk},
                )
            )

    template = 'proofing/request_typesetting_changes.html'
    context = {
        'article': article,
        'proofing_task': proofing_task,
        'typesetters': core_models.AccountRole.objects.filter(role__slug='typesetter', journal=article.journal),
        'user': user if request.POST else None,
        'galleys': galleys if request.POST else None,
        'form': form,
        'comments': comments,
    }

    return render(request, template, context)


@proofing_manager_for_article_required
def notify_typesetter_changes(request, article_id, proofing_task_id, typeset_task_id):
    """
    Optionally, we can send the typesetter a notification
    :param request: HttpRequest object
    :param article_id: Article PK
    :param proofing_task_id: ProofingTask PK
    :param typeset_task_id: TypesetterProofingTask PK
    :return: HttpRedirect or HttpResponse
    """
    article = get_object_or_404(submission_models.Article, pk=article_id)
    proofing_task = get_object_or_404(models.ProofingTask, pk=proofing_task_id)
    typeset_task = get_object_or_404(models.TypesetterProofingTask, pk=typeset_task_id)
    notification_email_content = logic.get_notify_typesetter(request, article, proofing_task, typeset_task)

    if request.POST:
        notification_email_content = request.POST.get('content_email', None)
        typeset_task.notified = True
        typeset_task.save()

        kwargs = {'request': request,
                  'typeset_task': typeset_task,
                  'article': article,
                  'user_content_message': notification_email_content,
                  'skip': True if 'skip' in request.POST else False,
                  }

        event_logic.Events.raise_event(event_logic.Events.ON_PROOFING_TYPESET_CHANGES_REQUEST,
                                       task_object=article,
                                       **kwargs)
        return redirect(reverse('proofing_article', kwargs={'article_id': article.pk}))

    template = 'proofing/notify_typesetter_changes.html'
    context = {
        'article': article,
        'proofing_task': proofing_task,
        'typeset_task': typeset_task,
        'notification_email_content': notification_email_content,
    }

    return render(request, template, context)


@typesetter_for_corrections_required
def typesetting_corrections(request, typeset_task_id):
    """
    Allows a typesetter to undertake corrections
    :param request: HttpRequest object
    :param typeset_task_id: TypesetterProofingTask PK
    :return: HttpRedirect or HttpResponse
    """
    typeset_task = get_object_or_404(
        models.TypesetterProofingTask.active_objects,
        pk=typeset_task_id,
        completed__isnull=True,

    )
    article = typeset_task.proofing_task.round.assignment.article
    form = forms.CompleteCorrections(instance=typeset_task)

    if request.POST:
        form = forms.CompleteCorrections(request.POST, instance=typeset_task)

        if form.is_valid():
            typeset_task = form.save(commit=False)
            typeset_task.completed = timezone.now()
            typeset_task.save()

            kwargs = {'article': article, 'typeset_task': typeset_task, 'request': request}
            event_logic.Events.raise_event(
                event_logic.Events.ON_CORRECTIONS_COMPLETE,
                task_object=article,
                **kwargs,
            )

            messages.add_message(request, messages.INFO, 'Corrections task complete')
            return redirect(reverse('proofing_correction_requests'))

    template = 'proofing/typesetting/typesetting_corrections.html'
    context = {
        'typeset_task': typeset_task,
        'article': article,
        'form': form,
    }

    return render(request, template, context)


@proofing_manager_for_article_required
def acknowledge(request, article_id, model_name, model_pk):
    """
    Acks a ProofingTask or TypesetterProofingTask
    :param request: HttpRequest object
    :param article_id: Article object PK
    :param model_name: string, name of a model
    :param model_pk: int, PK of model
    :return: HttpRedirect or HttpResponse
    """
    model, model_object = logic.get_model_and_object(model_name, model_pk)
    article = get_object_or_404(submission_models.Article, pk=article_id)
    text = logic.get_ack_message(request, article, model_name, model_object)

    if request.POST:
        message = request.POST.get('content_email', None)
        kwargs = {'request': request,
                  'article': article,
                  'user_message': message,
                  'model_object': model_object,
                  'model_name': model_name,
                  'skip': True if 'skip' in request.POST else False}
        event_logic.Events.raise_event(event_logic.Events.ON_PROOFING_ACK, task_object=article, **kwargs)
        model_object.acknowledged = timezone.now()
        model_object.save()
        return redirect(reverse('proofing_article', kwargs={'article_id': article.pk}))

    template = 'proofing/acknowledge.html'
    context = {
        'model': model,
        'model_object': model_object,
        'model_name': model_name,
        'text': text,
        'article': article,
    }

    return render(request, template, context)


@proofing_manager_for_article_required
def complete_proofing(request, article_id):
    """
    Allows a proofing manager to mark proofing a complete
    :param request: HttpRequest object
    :param article_id: Article object PK
    :return: HttpResponse object
    """
    article = get_object_or_404(submission_models.Article,
                                stage=submission_models.STAGE_PROOFING,
                                pk=article_id)
    message = logic.get_complete_proofing_message(request, article)

    if request.POST:
        message = request.POST.get('content_email')
        article.stage = submission_models.STAGE_READY_FOR_PUBLICATION
        article.proofingassignment.completed = timezone.now()
        article.save()

        journal_models.FixedPubCheckItems.objects.get_or_create(article=article)

        kwargs = {'request': request, 'article': article, 'user_message': message,
                  'skip': True if 'skip' in request.POST else False}
        event_logic.Events.raise_event(event_logic.Events.ON_PROOFING_COMPLETE, task_object=article, **kwargs)

        if request.journal.element_in_workflow(element_name='proofing'):
            workflow_kwargs = {'handshake_url': 'proofing_list', 'request': request, 'article': article,
                               'switch_stage': True}
            return event_logic.Events.raise_event(event_logic.Events.ON_WORKFLOW_ELEMENT_COMPLETE, task_object=article,
                                                  **workflow_kwargs)
        else:
            return redirect(reverse('publish_article', kwargs={'article_id': article.pk}))

    template = 'proofing/complete_proofing.html'
    context = {
        'article': article,
        'message': message,
    }

    return render(request, template, context)


# Helper views


@proofreader_for_article_required
def new_note(request, proofing_task_id, galley_id):
    """
    Allows proofreaders to generate new notes against their Task.
    :param request: HttpRequest object
    :param proofing_task_id: ProofingTask object PK
    :param galley_id: Galley object PK
    :return: HttpResponse
    """
    if request.user.is_staff:
        proofing_task = get_object_or_404(models.ProofingTask, pk=proofing_task_id)
    else:
        proofing_task = get_object_or_404(models.ProofingTask,
                                          (Q(proofreader=request.user) |
                                           Q(round__assignment__proofing_manager=request.user)),
                                          pk=proofing_task_id)
    galley = get_object_or_404(core_models.Galley, pk=galley_id)

    if request.POST:
        note = request.POST.get('note')
        note = models.Note.objects.create(
            galley=galley,
            creator=request.user,
            text=note,
        )

        proofing_task.notes.add(note)

        return_dict = {'id': note.pk, 'note': note.text, 'initials': note.creator.initials(),
                       'date_time': note.date_time.strftime("%Y-%m-%d %H:%i"),
                       'html': logic.create_html_snippet(note, proofing_task, galley)}

    else:

        return_dict = {'error': 'This request must be made with POST'}

    return HttpResponse(json.dumps(return_dict), content_type="application/json")


@proofreader_for_article_required
def delete_note(request, proofing_task_id, galley_id):
    """
    Allows Proofreader to delete a note
    :param request: HttpRequest object
    :param proofing_task_id: ProofingTask object PK
    :param galley_id: Galley object PK
    :return: HttpResponse
    """
    if request.user.is_staff:
        get_object_or_404(models.ProofingTask, pk=proofing_task_id)
    else:
        get_object_or_404(models.ProofingTask,
                          (Q(proofreader=request.user) |
                           Q(round__assignment__proofing_manager=request.user)),
                          pk=proofing_task_id)

    if request.POST:
        note_id = request.POST.get('note_id')
        note = get_object_or_404(models.Note, galley__pk=galley_id, pk=note_id)
        note.delete()

        return_dict = {'id': note.pk, 'deleted': True}

    else:
        return_dict = {'deleted': False}

    return HttpResponse(json.dumps(return_dict), content_type="application/json")


@proofreader_for_article_required
def proofing_download(request, proofing_task_id, file_id):
    """
    Serves a galley for proofreader
    """
    proofing_task = get_object_or_404(models.ProofingTask, pk=proofing_task_id)
    file = get_object_or_404(core_models.File, pk=file_id)

    if file in proofing_task.galley_files():
        return files.serve_file(request, file, proofing_task.round.assignment.article)
    else:
        messages.add_message(request, messages.WARNING, 'Requested file is not a galley for proofing')
        return redirect(request.META.get('HTTP_REFERER'))


@proofreader_for_article_required
def preview_figure(request, proofing_task_id, galley_id, file_name):
    galley = get_object_or_404(core_models.Galley, pk=galley_id, article__journal=request.journal)
    return article_figure(request, galley.article.pk, galley_id, file_name)
