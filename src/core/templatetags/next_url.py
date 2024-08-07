from django import template
from core.logic import reverse_with_next

register = template.Library()

@register.simple_tag(takes_context=True)
def url_with_next(context, url_name, *args, **kwargs):
    request = context.get('request')
    return reverse_with_next(url_name, request, *args, **kwargs)
