from django import template
from django.utils.html import mark_safe

register = template.Library()


@register.filter(name='bool_fa')
def bool_fa(boolean):
    if boolean:
        return mark_safe('<i class="fa fa-check-circle"></i>')
    else:
        return mark_safe('<i class="fa fa-times-circle"></i>')
