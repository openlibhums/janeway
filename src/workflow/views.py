from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.http import require_POST

from security.decorators import editor_user_required, has_journal
from submission import models as submission_models
from workflow import logic
from utils import models as utils_models
from events import logic as event_logic


@has_journal
@editor_user_required
def manage_article_workflow(request, article_id):
    """
    Presents an interface for an Editor user to move an article back along its workflow.
    :param request: HttpRequest object
    :param article_id: Article pbject PK
    :return: HttpResponse or HttpRedirect
    """

    article = get_object_or_404(
        submission_models.Article,
        pk=article_id,
        journal=request.journal
    )

    if request.POST:
        if 'stage_to' in request.POST:
            stage_to = request.POST.get('stage_to')
            stages_to_process = logic.move_to_stage(
                article.stage,
                stage_to,
                article,
            )

            stages_string = ', '.join(stages_to_process)

            messages.add_message(
                request,
                messages.INFO,
                'Processing: {}'.format(stages_string),
            )
        elif 'archive' in request.POST:
            utils_models.LogEntry.add_entry(
                types='Workflow',
                description='Article has been archived.',
                level='Info',
                actor=request.user,
                target=article,
            )
            article.stage = submission_models.STAGE_ARCHIVED
            article.save()
            messages.add_message(
                request,
                messages.SUCCESS,
                'Article has been archived.',
            )

        return redirect(
            reverse(
                'manage_article_workflow',
                kwargs={'article_id': article.pk}
            )
        )

    template = 'workflow/manage_article_workflow.html'
    context = {
        'article': article,
    }

    return render(request, template, context)


@require_POST
@has_journal
@editor_user_required
def move_to_next_workflow_element(request, article_id):
    article = get_object_or_404(
        submission_models.Article,
        pk=article_id,
        journal=request.journal
    )

    current_stage = request.POST.get('current_stage', None)
    if current_stage != article.stage:
        messages.add_message(
            request,
            messages.ERROR,
            'Could not change stage or duplicate request.',
        )
        return redirect(article.current_workflow_element_url)

    workflow_kwargs = {
        'handshake_url': article.current_workflow_element.handshake_url,
        'request': request,
        'article': article,
        'switch_stage': True
    }

    return event_logic.Events.raise_event(
        event_logic.Events.ON_WORKFLOW_ELEMENT_COMPLETE,
        task_object=article,
        **workflow_kwargs,
    )
