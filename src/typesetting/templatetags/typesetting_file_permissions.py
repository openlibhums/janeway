from django import template

from typesetting import security

register = template.Library()


@register.simple_tag(takes_context=True)
def can_manage_file(context, file_object):
    request = context['request']
    return security.can_manage_file(request, file_object)