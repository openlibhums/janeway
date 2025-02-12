from django import template

from typesetting import models

register = template.Library()


@register.simple_tag(takes_context=True)
def article_user_proofing_tasks(context):
    request = context['request']
    article = context['article']

    return models.GalleyProofing.objects.filter(
        round__article=article,
        round__article__authors=request.user,
        proofreader=request.user,
        completed__isnull=True,
        cancelled=False,
    )