from collections import OrderedDict
from importlib import import_module

from django.urls import reverse
from django.shortcuts import redirect
from django.http import Http404
from django.conf import settings

from core import models
from submission import models as submission_models


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
    current_element = workflow.elements.get(handshake_url=handshake_url)

    try:
        workflow_elements = workflow.elements.all()
        index = list(workflow_elements).index(current_element) + 1
        next_element = workflow_elements[index]

        if switch_stage:
            article.stage = next_element.stage
            article.save()

        return redirect(reverse(next_element.handshake_url, kwargs={'article_id': article.pk}))
    except BaseException as e:
        print(e)
        return redirect(reverse('core_dashboard'))


def set_stage(article):
    """
    Sets the article stage on submission to the first element in the workflow.
    :param article: Article object
    :return: None
    """

    workflow = models.Workflow.objects.get(journal=article.journal)
    first_element = workflow.elements.all()[0]
    article.stage = first_element.stage
    article.save()


def create_default_workflow(journal):
    """
    Creates a default workflow for a given journal
    :param journal: Journal object
    :return: None
    """

    workflow = models.Workflow.objects.get_or_create(journal=journal)

    for element in models.BASE_ELEMENTS:
        e = models.WorkflowElement.objects.get_or_create(journal=journal,
                                                         element_name=element.get('name'),
                                                         handshake_url=element['handshake_url'],
                                                         stage=element['stage'])

        workflow.elements.add(e)

    return workflow


def articles_in_workflow_stages(request):
    """
    Returns an ordered dict {'stage': [articles]}
    :param request: HttpRequest object
    :return: Dictionary
    """

    workflow = request.journal.workflow()
    workflow_list = {}

    for element in workflow.elements.all():
        element_dict = {}

        try:
            settings_module = import_module(settings.WORKFLOW_PLUGINS[element.element_name])

            element_dict['articles'] = submission_models.Article.objects.filter(stage=element.stage)
            element_dict['name'] = element.element_name
            element_dict['template'] = settings_module.KANBAN_CARD

            workflow_list[element.element_name] = element_dict
        except KeyError as e:
            if settings.DEBUG:
                print(e)

    return workflow_list

