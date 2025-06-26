from django import template
from django.urls import reverse
from core.logic import reverse_with_next, reverse_with_query
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

    Note that `full_page_path` can be set by `url_with_full_page_path`.
    """
    full_page_path = context.get('full_page_path', '')
    if full_page_path:
        next_url = full_page_path
    else:
        request = context.get('request')
        next_url = request.get_full_path()
    return reverse_with_next(url_name, next_url, args=args, kwargs=kwargs)


@register.simple_tag(takes_context=True)
def url_with_full_page_path(context, url_name, *args, **kwargs):
    """
    Use this to reverse a URL pointing to a view that returns a partial page.
    It provides key information about the window state, namely the
    path of the full page, which is useful in creating multi-page user flows.

    The targeted view must handle the GET parameter `full_page_path`
    by putting it in the view `context`. From there it can be accessed by
    `url_with_return` in partial page templates.
    """
    request = context.get('request')
    query_params = {
        'full_page_path': request.get_full_path()
    }
    return reverse_with_query(
        url_name,
        args=args,
        kwargs=kwargs,
        query_params=query_params,
    )
