from django import template

register = template.Library()


@register.filter
def classname(obj):
    try:
        return obj.__class__.__name__
    except AttributeError:
        return ''
