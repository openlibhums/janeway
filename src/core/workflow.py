from importlib import import_module

from django.urls import reverse
from django.shortcuts import redirect
from django.http import Http404
from django.conf import settings
from django.urls.resolvers import NoReverseMatch
from django.contrib import messages
from django.utils.text import capfirst

from core import models
from review.logic import assign_editor
from submission import models as submission_models
from utils.logger import get_logger
from utils.shared import clear_cache

logger = get_logger(__name__)


ELEMENT_STAGES = {
    'review': submission_models.REVIEW_STAGES,
    'copyediting': submission_models.COPYEDITING_STAGES,
    'production': [submission_models.STAGE_TYPESETTING],
    'proofing': [submission_models.STAGE_PROOFING],
    'prepublication': [submission_models.STAGE_READY_FOR_PUBLICATION]
}

STAGES_ELEMENTS = {
    submission_models.STAGE_ASSIGNED: 'review',
    submission_models.STAGE_UNDER_REVIEW: 'review',
    submission_models.STAGE_UNDER_REVISION: 'review',

    submission_models.STAGE_EDITOR_COPYEDITING: 'copyediting',
    submission_models.STAGE_AUTHOR_COPYEDITING: 'copyediting',
    submission_models.STAGE_FINAL_COPYEDITING: 'copyediting',

    submission_models.STAGE_TYPESETTING: 'production',
    submission_models.STAGE_PROOFING: 'proofing',
    submission_models.STAGE_READY_FOR_PUBLICATION: 'prepublication',
}


def workflow_element_complete(**kwargs):
    """
    Handler for workflow complete event
    :param kwargs: A dict containing three keys handshake_url, request, article and optionally switch_stage
    :return: HttpRedirect
    """

    handshake_url = kwargs.get('handshake_url')
    request = kwargs.get('request')
    article = kwargs.get('article')
    switch_stage = kwargs.get('switch_stage')

    if not handshake_url or not request or not article:
        raise Http404

    return workflow_next(handshake_url, request, article, switch_stage)


def workflow_next(handshake_url, request, article, switch_stage=False):
    """
    Works out what the next workflow element should be so we can redirect the user there.
    :param handshake_url: Current workflow element's handshake url
    :param request: HttpRequest object
    :param article: Article object
    :return: HttpRedirect
    """

    workflow = models.Workflow.objects.get(journal=request.journal)
    workflow_elements = workflow.elements.all()

    if handshake_url == 'submit_review':
        set_stage(article)
        clear_cache()
        return redirect(reverse('core_dashboard'))

    current_element = workflow.elements.get(handshake_url=handshake_url)

    try:
        try:
            index = list(workflow_elements).index(current_element) + 1
            next_element = workflow_elements[index]
        except IndexError:
            # An index error will occur here when the workflow is complete
            return redirect(reverse('manage_archive_article', kwargs={'article_id': article.pk}))

        if switch_stage:
            log_stage_change(article, next_element)
            clear_cache()
            article.stage = next_element.stage
            article.save()

        try:
            response = redirect(reverse(
                next_element.handshake_url,
                kwargs={'article_id': article.pk},
            ))
        except NoReverseMatch:
            response = redirect(reverse(next_element.handshake_url))

    except Exception as e:
        logger.exception(e)
        response = redirect(reverse('core_dashboard'))

    if response.status_code == 302:
        response = redirect(reverse('core_dashboard'))

    messages.add_message(
        request,
        messages.SUCCESS,
        '%s stage completed for article: %d'
        '' % (capfirst(current_element.element_name), article.pk),
    )

    return response


def log_stage_change(article, next_element):
    """
    Crates a WorkflowLog entry for this change.
    :param article: Article object
    :param next_element: WorkflowElement object
    :return: None
    """
    models.WorkflowLog.objects.create(article=article, element=next_element)


def set_stage(article):
    """
    Sets the article stage on submission to the first element in the workflow.
    :param article: Article object
    :return: None
    """
    workflow = models.Workflow.objects.get(journal=article.journal)
    first_element = workflow.elements.all()[0]
    log_stage_change(article, first_element)
    article.stage = first_element.stage
    article.save()


def create_default_workflow(journal):
    """
    Creates a default workflow for a given journal
    :param journal: Journal object
    :return: None
    """

    workflow, c = models.Workflow.objects.get_or_create(journal=journal)

    for index, element in enumerate(models.BASE_ELEMENTS):
        e, c = models.WorkflowElement.objects.get_or_create(journal=journal,
                                                            element_name=element.get('name'),
                                                            handshake_url=element['handshake_url'],
                                                            stage=element['stage'],
                                                            jump_url=element['jump_url'],
                                                            article_url=element['article_url'],
                                                            defaults={'order': index})

        workflow.elements.add(e)

    return workflow


def articles_in_workflow_plugins(request):
    """
    Returns an ordered dict {'stage': [articles]}
    :param request: HttpRequest object
    :return: Dictionary
    """

    workflow = request.journal.workflow()
    workflow_list = {}

    for element in workflow.elements.all():
        if element.element_name in settings.WORKFLOW_PLUGINS:
            try:
                settings_module = import_module(settings.WORKFLOW_PLUGINS[element.element_name])

                element_dict = {
                    'articles': submission_models.Article.objects.filter(
                        stage=element.stage,
                        journal=request.journal,
                    ),
                    'name': element.element_name,
                    'template': settings_module.KANBAN_CARD,
                }

                workflow_list[element.element_name] = element_dict
            except (KeyError, AttributeError) as e:
                logger.error(e)

    return workflow_list


def core_workflow_element_names():
    return [element.get('name') for element in models.BASE_ELEMENTS]


def element_names(elements):
    return [element.element_name for element in elements]


def remove_element(request, journal_workflow, element):
    """
    Checks if there are any articles in the current stage and
    blocks its removal if there are.
    :param request:
    :param journal_workflow:
    :param element:
    :return:
    """
    stages = ELEMENT_STAGES.get(element.element_name, None)

    articles = submission_models.Article.objects.filter(
        stage__in=stages,
        journal=request.journal,
    )

    if articles:
        messages.add_message(
            request,
            messages.WARNING,
            'Element cannot be removed as there are {0}'
            ' articles in this stage.'.format(articles.count())
        )
    else:
        journal_workflow.elements.remove(element)
        messages.add_message(
            request,
            messages.SUCCESS,
            'Element removed from workflow.'
        )


def workflow_plugin_settings(element):
    """
    Gets the plugin settings module for a plugin and returns useful settings
    :param element: a WorkflowElement object
    :return: dict of useful settings
    """
    try:
        settings_module = import_module(
            settings.WORKFLOW_PLUGINS[element.element_name],
        )

        return {
            'display_name': getattr(settings_module, 'DISPLAY_NAME', ''),
            'description': getattr(settings_module, 'DESCRIPTION', ''),
            'kanban_card': getattr(settings_module, 'KANBAN_CARD', ''),
            'dashboard_template': getattr(
                settings_module, 'DASHBOARD_TEMPLATE', ''
            )
        }

    except (ImportError, KeyError) as e:
        logger.error(e)

    return {}


def workflow_auto_assign_editors(**kwargs):
    """
    Handler for auto assignment of editors
    :param kwargs: A dict containing three keys handshake_url, request, article and optionally switch_stage
    """
    article = kwargs.get('article')
    request = kwargs.get('request')
    skip = kwargs.get('skip', False)

    if article and article.section and article.section.auto_assign_editors:
        section = article.section

        assignment_type = "editor"
        for editor in section.editors.all():
            assign_editor(article, editor, assignment_type, request, skip)

        assignment_type = "section-editor"
        for s_editor in section.section_editors.all():
            assign_editor(article, s_editor, assignment_type, request, skip)
