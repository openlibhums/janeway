from itertools import chain
from django import template

register = template.Library()


@register.simple_tag(name='chain')
def chain_tag(*iterables):
    return chain(*iterables)
