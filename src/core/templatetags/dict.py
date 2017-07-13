from django import template
from pprint import pprint

register = template.Library()


@register.filter(name='get')
def get(o, index):
    try:
        return o[str(index)]
    except BaseException:
        return 'INVALID STRING'
