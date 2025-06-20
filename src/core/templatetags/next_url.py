from django import template
from django.urls import reverse
from core.logic import reverse_with_next, reverse_with_full_page_path
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
    A template tag to use when reversing a URL for a partial view
    before accessing it with JavaScript. This is what it makes possible:
      1. passes full_page_path to the partial view as a GET parameter
      2. the partial view puts it into the context dictionary
      3. the partial view's template calls url_with_return as normal
      4. url_with_return checks for it and uses it rather than its own request.get_full_path
    Without this pattern, url_with_return would encode a next parameter
    that points to the partial view, not the full page, resulting in the user
    loading up a bare HTML snippet with no nav or CSS on completing a task.
    """
    request = context.get('request')
    full_page_path = request.get_full_path()
    return reverse_with_full_page_path(
        url_name,
        full_page_path,
        args=args,
        kwargs=kwargs,
    )
