from django import template

from core.middleware import GlobalRequestMiddleware
from security import logic
from submission import models
from utils import setting_handler

register = template.Library()

# General role-based checks


@register.simple_tag(takes_context=True)
def is_author(context):
    request = context['request']
    return request.user.is_author(request)


@register.simple_tag(takes_context=True)
def is_editor(context):
    request = context['request']
    if request.user.is_anonymous:
        return False
    return request.user.is_editor(request)


@register.simple_tag(takes_context=True)
def is_section_editor(context):
    request = context['request']
    if request.user.is_anonymous:
        return False
    return request.user.is_section_editor(request)


@register.simple_tag(takes_context=True)
def is_any_editor(context):
    request = context['request']
    if request.user.is_anonymous:
        return False
    return request.user.has_an_editor_role(request)


@register.simple_tag(takes_context=True)
def is_production(context):
    request = context['request']
    return request.user.is_production(request)


@register.simple_tag(takes_context=True)
def is_reviewer(context):
    request = context['request']
    return request.user.is_reviewer(request)


@register.simple_tag(takes_context=True)
def is_proofreader(context):
    request = context['request']
    return request.user.is_proofreader(request)

# File-based checks


@register.simple_tag(takes_context=True)
def can_edit_file(context, file_object, article_object):
    return logic.can_edit_file(context['request'], context['request'].user, file_object, article_object)


@register.simple_tag(takes_context=True)
def can_view_file_history(context, file_object, article_object):
    return logic.can_view_file_history(context['request'], context['request'].user, file_object, article_object)


@register.simple_tag(takes_context=True)
def can_view_file(context, file_object):
    return logic.can_view_file(context['request'], context['request'].user, file_object)


@register.simple_tag(takes_context=True)
def is_author(context):
    request = context['request']
    return request.user.is_author(request)


@register.simple_tag(takes_context=True)
def is_repository_manager(context):
    request = context['request']
    return request.user.is_repository_manager(request.repository)


@register.simple_tag(takes_context=True)
def is_preprint_editor(context):
    request = context['request']
    return request.user.is_preprint_editor(request)


def can_see_pii(request, article):
    # Before doing anything, check the setting is enabled:
    se_pii_filter_enabled = setting_handler.get_setting(
        setting_group_name='permission',
        setting_name='se_pii_filter',
        journal=article.journal,
    ).processed_value

    if not se_pii_filter_enabled:
        return False

    # Check if the user is an SE and return an anonymised value.
    # If the user is not a section editor we assume they have permission
    # to view the actual value.
    stages = [
        models.STAGE_UNASSIGNED,
        models.STAGE_UNDER_REVIEW,
        models.STAGE_UNDER_REVISION,
    ]
    if request.user in article.section_editors() and article.stage in stages:
        return True
    return False


@register.filter
def se_can_see_pii(value, article):
    request = GlobalRequestMiddleware.get_current_request()

    if can_see_pii(request, article):
        return 'Value Anonymised'
    else:
        return value


@register.simple_tag(takes_context=True)
def can_see_pii_tag(context, article):
    request = context.get('request')

    if can_see_pii(request, article):
        return False
    else:
        return True



