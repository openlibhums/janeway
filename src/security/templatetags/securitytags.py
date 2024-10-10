from django import template

from core.middleware import GlobalRequestMiddleware
from security import logic
from django.utils.translation import gettext_lazy as _

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


@register.filter
def se_can_see_pii(value, article):
    request = GlobalRequestMiddleware.get_current_request()

    if logic.can_see_pii(request, article):
        return value
    else:
        return _('[Anonymised data]')


@register.simple_tag(takes_context=True)
def can_see_pii_tag(context, article):
    request = context.get('request')

    if logic.can_see_pii(request, article):
        return True
    else:
        return False



