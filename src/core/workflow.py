from django.urls import reverse
from django.shortcuts import redirect

from core import models


def workflow_next(handshake_url, request, article):

    workflow = models.Workflow.objects.get(journal=request.journal)
    current_element = workflow.elements.get(handshake_url=handshake_url)
    try:
        workflow_elements = workflow.elements.all()
        index = workflow_elements.index(current_element) + 1
        next_element = workflow_elements[index]
        return redirect(reverse(next_element.handshake_url, kwargs={'article_id': article.pk}))
    except BaseException as e:
        print(e)
        return redirect(reverse('core_dashboard'))


def set_stage(stage, article):
    workflow = models.Workflow.objects.get(journal=article.journal)
    first_element = workflow.elements.all()[0]
    article.stage = first_element.stage
    article.save()
