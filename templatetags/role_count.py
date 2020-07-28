from django import template

from plugins.typesetting import models, plugin_settings
from submission import models as submission_models

register = template.Library()


@register.simple_tag(takes_context=True)
def typesetting_tasks_count(context):
    request = context['request']
    return models.TypesettingAssignment.objects.filter(
        typesetter=request.user,
        round__article__journal=request.journal,
        completed__isnull=True,
        cancelled__isnull=True,
    ).count()


@register.simple_tag(takes_context=True)
def proofreading_tasks_count(context):
    request = context['request']
    return models.GalleyProofing.objects.filter(
        round__article__journal=request.journal,
        proofreader=request.user,
        completed__isnull=True,
        cancelled=False,
    ).count()


@register.simple_tag(takes_context=True)
def articles_in_stage_count(context):
    request = context['request']

    return submission_models.Article.objects.filter(
        journal=request.journal,
        stage=plugin_settings.STAGE,
    ).count()
