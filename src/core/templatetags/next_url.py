from django import template
from django.urls import reverse
from core.logic import reverse_with_next
from urllib.parse import quote


register = template.Library()

@register.simple_tag(takes_context=True)
def url_with_next(context, url_name, next_url_name='', *args, **kwargs):
    """
    A template tag to use instead of 'url' when you want
    the reversed URL to include the same 'next' parameter that
    already exists in the GET or POST data of the request,
    or you want to introduce a new next url by Django URL name.
    """
    if next_url_name:
        next_url = reverse(next_url_name)
    else:
        next_url = ''
    request = context.get('request')
    return reverse_with_next(
        url_name,
        request,
        next_url=next_url,
        *args,
        **kwargs,
    )


@register.simple_tag(takes_context=True)
def url_with_return(context, url_name, *args, **kwargs):
    """
    A template tag to use instead of 'url' when you want
    the reversed URL to include a new 'next' parameter that
    contains the full path of the current request.
    """
    request = context.get('request')
    next_url = quote(request.get_full_path())
    return reverse_with_next(
        url_name,
        request,
        next_url=next_url,
        *args,
        **kwargs,
    )
