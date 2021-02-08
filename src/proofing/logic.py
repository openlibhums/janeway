__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.db.models import Q
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse
from django.template.loader import get_template
from django.shortcuts import get_object_or_404

from core import models as core_models, files
from events import logic as event_logic
from utils import render_template, models as utils_models
from proofing import models


def handle_closing_active_task(request, article):
    if article.proofingassignment.current_proofing_round().has_active_tasks:
        for task in article.proofingassignment.current_proofing_round().proofingtask_set.all():
            if not task.completed:
                task.completed = timezone.now()
                task.cancelled = True
                task.save()

                kwargs = {
                    'article': article,
                    'proofing_task': task,
                    'request': request,
                    'user_content_message': request.POST.get('note_to_proofreaders', None)
                }
                event_logic.Events.raise_event(event_logic.Events.ON_CANCEL_PROOFING_TASK,
                                               task_object=article,
                                               **kwargs)
    else:
        messages.add_message(request, messages.INFO, 'There are no active tasks.')


def get_all_possible_proofers(journal, article):
    active_proofreaders = article.proofingassignment.current_proofing_round().active_proofreaders

    proofers = core_models.AccountRole.objects.filter(
        (Q(role__slug='editor') | Q(role__slug='proofreader')) & Q(journal=journal)
    ).exclude(user__in=article.authors.all()).exclude(user__in=active_proofreaders)
    all_possible_proofers = [{'user': role.user, 'role': role.role.slug} for role in proofers]

    for author in article.authors.all():
        if author not in active_proofreaders:
            all_possible_proofers.append({'user': author, 'role': 'author'})

    return all_possible_proofers


def get_user_from_post(request, article=False, typesetter=False):
    user_id = request.POST.get('proofreader')

    if user_id:
        user = core_models.Account.objects.get(pk=user_id)

        # check if the user is an author of this paper
        if article and not typesetter and user in article.authors.all():
            return user

        # return None if we aren't checking for typesetting and the user isn't a proofreder
        elif not typesetter and not (
            user.is_proofreader(request)
            or user.is_editor(request)
        ):
            return None

        # return None if we are checking for a typesetter and the user isn't a typesetter
        elif typesetter and not user.is_typesetter(request):
            return None
    else:
        user = None

    return user


def get_galleys_from_post(request):
    galley_id_list = request.POST.getlist('galleys_for_proofing')

    return [core_models.Galley.objects.get(pk=galley_id) for galley_id in galley_id_list]


def get_files_from_post(request):
    file_id_list = request.POST.getlist('files_for_proofing')

    return [core_models.File.objects.get(pk=file_id) for file_id in file_id_list]


def get_notify_proofreader(request, article, proofing_task):
    proofing_url = request.journal.site_url(reverse("proofing_requests"))
    context = {
        'proofing_requests_url': proofing_url,
        'article': article,
        'proofing_task': proofing_task,
    }

    return render_template.get_message_content(request, context, 'notify_proofreader_assignment')


def get_notify_typesetter(request, article, proofing_task, typeset_task):
    proofing_url = request.journal.site_url(reverse("proofing_correction_requests"))
    context = {
        'proofing_requests_url': proofing_url,
        'article': article,
        'proofing_task': proofing_task,
        'typesetter_proofing_task': typeset_task,
    }

    return render_template.get_message_content(request, context, 'notify_typesetter_proofing_changes')


def create_html_snippet(note, proofing_task, galley):
    template = get_template('proofing/note_snip.html')
    html_content = template.render({'note': note, 'proofing_task': proofing_task, 'galley': galley})

    return html_content


def get_tasks(request):
    new = models.ProofingTask.objects.filter(
        completed__isnull=True,
        accepted__isnull=True,
        cancelled=False,
        proofreader=request.user,
        round__assignment__article__journal=request.journal,
    )
    active = models.ProofingTask.objects.filter(
        completed__isnull=True,
        accepted__isnull=False,
        cancelled=False,
        proofreader=request.user,
        round__assignment__article__journal=request.journal,
    )
    completed = models.ProofingTask.objects.filter(
        completed__isnull=False,
        cancelled=False,
        proofreader=request.user,
        round__assignment__article__journal=request.journal,
    )

    return new, active, completed


def get_typesetting_tasks(request):
    new_typesetting = models.TypesetterProofingTask.objects.filter(
        completed__isnull=True,
        accepted__isnull=True,
        cancelled=False,
        typesetter=request.user,
        proofing_task__round__assignment__article__journal=request.journal,
    )
    active_typesetting = models.TypesetterProofingTask.objects.filter(
        completed__isnull=True,
        accepted__isnull=False,
        cancelled=False,
        typesetter=request.user,
        proofing_task__round__assignment__article__journal=request.journal,
    )
    completed_typesetting = models.TypesetterProofingTask.objects.filter(
        completed__isnull=False,
        cancelled=False,
        typesetter=request.user,
        proofing_task__round__assignment__article__journal=request.journal,
    )

    return new_typesetting, active_typesetting, completed_typesetting


def handle_proof_decision(request, proofing_task_id, decision):
    proofing_task = get_object_or_404(models.ProofingTask,
                                      proofreader=request.user,
                                      pk=proofing_task_id)
    if decision == 'accept':
        proofing_task.accepted = timezone.now()
    elif decision == 'decline':
        proofing_task.completed = timezone.now()
    proofing_task.save()
    kwargs = {'request': request, 'proofing_task': proofing_task, 'decision': decision}
    event_logic.Events.raise_event(event_logic.Events.ON_PROOFREADER_TASK_DECISION,
                                   task_object=proofing_task.round.assignment.article,
                                   **kwargs)
    messages.add_message(request, messages.INFO, 'Proofing Task {0} decision: {1}'.format(proofing_task_id, decision))


def handle_typeset_decision(request, typeset_task_id, decision):
    typeset_task = get_object_or_404(
        models.TypesetterProofingTask,
        typesetter=request.user,
        pk=typeset_task_id,
        proofing_task__round__assignment__article__journal=request.journal,
    )
    if decision == 'accept':
        typeset_task.accepted = timezone.now()
    elif decision == 'decline':
        typeset_task.completed = timezone.now()
    typeset_task.save()
    kwargs = {'request': request, 'typeset_task': typeset_task, 'decision': decision}
    event_logic.Events.raise_event(event_logic.Events.ON_PROOFING_TYPESET_DECISION,
                                   task_object=typeset_task.proofing_task.round.assignment.article,
                                   **kwargs)
    messages.add_message(request, messages.INFO, 'Typeset Task {0} decision: {1}'.format(typeset_task_id, decision))


def get_model_and_object(model_name, model_pk):
    model = None
    if model_name == 'proofing':
        model = models.ProofingTask
    elif model_name == 'correction':
        model = models.TypesetterProofingTask

    if model:
        return [model, get_object_or_404(model, pk=model_pk, acknowledged__isnull=True)]
    else:
        return [None, None]


def get_ack_message(request, article, model_name, model_object):
    if model_name == 'proofing':
        user = model_object.proofreader
    elif model_name == 'correction':
        user = model_object.typesetter
    else:
        user = None

    context = {
        'article': article,
        'user': user,
    }

    return render_template.get_message_content(request, context, 'thank_proofreaders_and_typesetters')


def get_complete_proofing_message(request, article):
    context = {
        'article': article,
        'proofing_assignment': article.proofingassignment,
    }

    return render_template.get_message_content(request, context, 'notify_editor_proofing_complete')


def get_typesetters(article, proofing_task):
    correction_tasks = models.TypesetterProofingTask.objects.filter(
        proofing_task=proofing_task,
        completed__isnull=True,
    )

    typesetters = [task.typesetter.pk for task in correction_tasks]

    return core_models.AccountRole.objects.filter(role__slug='typesetter', journal=article.journal).exclude(
        user__pk__in=typesetters)


def handle_annotated_galley_upload(request, proofing_task, article):
    uploaded_files = request.FILES.getlist('file')

    if uploaded_files:
        for file in uploaded_files:
            new_file = files.save_file_to_article(file, article, request.user)
            new_file.label = 'Annotated Proof'
            new_file.save()
            proofing_task.proofed_files.add(new_file)
            messages.add_message(request, messages.SUCCESS, 'Annotated file uploaded.')
        return None
    else:
        return 'uploadbox'


def add_reset_log_entry(request, proofing_task, article):
    """
    Adds a LogEntry when a proofing task is reset.
    :param request: HttpRequest object
    :param proofing_task: ProofingTask object
    :param article: Article object
    :return: None
    """

    description = '{user} reset proofing task {id} for article {title}'.format(
        user=request.user,
        id=proofing_task.pk,
        title=article.title,
    )

    utils_models.LogEntry.add_entry(
        types='Proofing Task Reset',
        description=description,
        level='Info',
        actor=request.user,
        request=request,
        target=article,
    )


def delete_round(article, round):
    """
    Deletes a round and checks if a new one needs to be generated.
    :param article: an Article object
    :param round: a ProofingRound object
    :return: None
    """
    round.delete()

    if not article.proofingassignment.proofinground_set.all():
        article.proofingassignment.add_new_proofing_round()

