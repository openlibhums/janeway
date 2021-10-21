from django import template
from django.utils.html import mark_safe

register = template.Library()


@register.filter(name='get')
def get(o, index):
    try:
        return o[str(index)]
    except BaseException:
        return 'INVALID STRING'


@register.simple_tag
def tag_get(o, index):
    try:
        return o[str(index)]
    except BaseException:
        return 'INVALID STRING'


@register.simple_tag(takes_context=True)
def context_get(context, key):
    try:
        return mark_safe(context[str(key)])
    except KeyError:
        return ''
