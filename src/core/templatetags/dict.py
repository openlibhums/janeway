from django import template

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
