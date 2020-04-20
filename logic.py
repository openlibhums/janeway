from django.db import transaction
from django.shortcuts import redirect, reverse
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages

from core import models as core_models, files
from events import logic as event_logic
from production import logic
from utils import render_template

from plugins.typesetting import models, plugin_settings
from plugins.typesetting.notifications import notify


def production_ready_files(article, file_objects=False):
    """
    Gathers a list of production ready files.
    :param article: an Article object
    :param file_objects: Boolean
    :return: a list of File type objects
    """
    submitted_ms_files = article.manuscript_files.filter(is_galley=False)
    copyeditted_files = logic.get_copyedit_files(article)

    if file_objects:
        file_pks = list()

        for file in submitted_ms_files:
            file_pks.append(file.pk)

        for file in copyeditted_files:
            file_pks.append(file.pk)

        return core_models.File.objects.filter(pk__in=file_pks)

    else:

        return {
            'Manuscript File': submitted_ms_files,
            'Copyedited File': copyeditted_files,
        }


def get_typesetters(journal):
    typesetter_pks = [
        role.user.pk for role in core_models.AccountRole.objects.filter(
            role__slug='typesetter',
            journal=journal,
        )
    ]

    return core_models.Account.objects.filter(pk__in=typesetter_pks)


def get_proofreaders(article, round, assignment=None):
    pks = list()
    current_proofer_pks = [
        p.proofreader.pk for p in round.galleyproofing_set.all()
    ]

    for author in article.authors.all():
        pks.append(author.pk)

    for proofreader in core_models.AccountRole.objects.filter(
        role__slug='proofreader',
        journal=article.journal
    ):
        pks.append(proofreader.user.pk)

    # If fetching for an assignment we want that user to remain in the list
    if assignment and assignment.proofreader.pk in pks:
        current_proofer_pks.remove(assignment.proofreader.pk)

    return core_models.Account.objects.filter(
        pk__in=pks,
    ).exclude(
        pk__in=current_proofer_pks,
    )


def get_typesetter_notification(assignment, article, request):
    context = {
        'article': article,
        'assignment': assignment,
    }
    return render_template.get_message_content(
        request,
        context,
        'typesetting_notify_typesetter',
    )


def get_proofreader_notification(assignment, article, request):
    context = {
        'article': article,
        'assignment': assignment,
    }
    return render_template.get_message_content(
        request,
        context,
        'typesetting_notify_proofreader',
    )


def handle_proofreader_file(request, assignment, article):
    uploaded_files = request.FILES.getlist('file')

    if uploaded_files:
        for file in uploaded_files:
            new_file = files.save_file_to_article(
                file,
                article,
                request.user,
            )
            new_file.label = 'Proofing File'
            new_file.save()
            assignment.annotated_files.add(new_file)
            messages.add_message(
                request,
                messages.SUCCESS,
                'Annotated file uploaded.',
            )


def new_typesetting_round(article, rounds, request):
    if not rounds:
        new_round = models.TypesettingRound.objects.create(
            article=article,
        )
    else:
        latest_round = rounds[0]
        latest_round.close(request.user)

        notify.event_typesetting_cancelled(
            latest_round.typesettingassignment,
            request,
        )

        new_round = models.TypesettingRound.objects.create(
            article=article,
            round_number=latest_round.round_number + 1,
        )

    return new_round


MISSING_GALLEYS = _("Article has no galleys")
MISSING_IMAGES = _("One or more Galleys are missing images")
OPEN_TASKS = _("One or more typesetting or proofing tasks haven't been closed")


def typesetting_pending_tasks(round):
    pending_tasks = []
    galleys = round.article.galley_set.all()
    if not galleys:
        pending_tasks.append(MISSING_GALLEYS)
    else:
        for galley in galleys:
            if galley.has_missing_image_files():
                pending_tasks.append(MISSING_IMAGES)
                break

    if round.has_open_tasks:
        pending_tasks.append(OPEN_TASKS)

    return pending_tasks


@transaction.atomic
def complete_typesetting(request, article):
    kwargs = {
        'request': request,
        'article': article,
    }

    event_logic.Events.raise_event(
        plugin_settings.ON_TYPESETTING_COMPLETE,
        task_object=article, **kwargs
    )
    if request.journal.element_in_workflow(element_name='Typesetting Plugin'):
        workflow_kwargs = {
            'handshake_url': 'typesetting_articles',
            'request': request,
            'article': article,
            'switch_stage': True,
        }

        return event_logic.Events.raise_event(
            event_logic.Events.ON_WORKFLOW_ELEMENT_COMPLETE,
            task_object=article,
            **workflow_kwargs)
    else:
        messages.add_message(
            request,
            messages.WARNING,
            'There was an error moving this article to the next stage.'
        )
        return redirect(
            reverse('core_dashboard')
        )


def get_next_element(handshake_url, request):
    workflow = core_models.Workflow.objects.get(journal=request.journal)
    workflow_elements = workflow.elements.all()

    current_element = workflow.elements.get(handshake_url=handshake_url)

    try:
        index = list(workflow_elements).index(current_element) + 1
        return workflow_elements[index]
    except IndexError:
        # An index error will occur here when the workflow is complete
        return None
