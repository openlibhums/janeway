from django import template

register = template.Library()


@register.filter
def latex_conform(value):
    return "{%s}" % value
