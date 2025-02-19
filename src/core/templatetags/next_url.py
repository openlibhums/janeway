from django import template
from django.urls import reverse
from core.logic import reverse_with_next
from urllib.parse import quote

register = template.Library()

@register.simple_tag(takes_context=True)
def url_with_next(context, url_name, *args, **kwargs):
    """
    A template tag to use instead of 'url' when you want
    the reversed URL to include the same 'next' parameter that
    already exists in the GET data of the request.
    """
    request = context.get('request')
    next_url = request.GET.get('next', '')
    return reverse_with_next(url_name, next_url, args=args, kwargs=kwargs)


@register.simple_tag(takes_context=True)
def url_with_return(context, url_name, *args, **kwargs):
    """
    A template tag to use instead of 'url' when you want
    the reversed URL to include a new 'next' parameter that
    contains the full and query string path of the current request.
    """
    request = context.get('request')
    next_url = request.get_full_path()
    return reverse_with_next(url_name, next_url, args=args, kwargs=kwargs)
