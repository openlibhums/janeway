from importlib import import_module

from django.urls import reverse
from django.shortcuts import redirect
from django.http import Http404
from django.conf import settings
from django.urls.resolvers import NoReverseMatch

from core import models
from submission import models as submission_models
from utils.shared import clear_cache


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
            return redirect(reverse(next_element.handshake_url, kwargs={'article_id': article.pk}))
        except NoReverseMatch:
            return redirect(reverse(next_element.handshake_url))
    except BaseException as e:
        print(e)
        return redirect(reverse('core_dashboard'))


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
                                                            defaults={'order': index,
                                                                      'article_url': element.get('article_url')})

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
