from django.urls import reverse
from django.shortcuts import redirect

from core import models


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
