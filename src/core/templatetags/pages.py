"""
Template tags for handling paginator objects
"""

from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def page_query(context, **kwargs):
    """Returns the current query string with kwargs replaced.

    Pagination links that hardcode ?page=n discard whatever search, filter and
    sort the reader already applied, sending them back to an unfiltered list.
    """
    request = context.get("request")
    query = request.GET.copy() if request else {}
    for key, value in kwargs.items():
        if value in (None, ""):
            query.pop(key, None)
        else:
            query[key] = value
    encoded = query.urlencode() if hasattr(query, "urlencode") else ""
    return "?{}".format(encoded) if encoded else "?"


@register.filter()
def slice_pages(current_page, slice_size=2):
    """Given a page and a slice size returns a slice of pages

    :current_page: A django.core.paginator.Page
    :slice_size: int
    """
    paginator = current_page.paginator
    slice_size = int(slice_size)
    first = max(1, current_page.number - slice_size)
    last = min(paginator.num_pages, current_page.number + slice_size)
    return [
        current_page.paginator.page(page_num) for page_num in range(first, last + 1)
    ]


@register.filter()
def slice_pages_with_first_last_ellipsis(current_page, slice_size=2):
    paginator = current_page.paginator
    page_set = []
    slice_size = int(slice_size)

    if current_page.number - slice_size > 1:
        page_set.append(paginator.page(1))
        if current_page.number - slice_size > 3:
            page_set.append("...")
        elif current_page.number - slice_size > 2:
            page_set.append(paginator.page(2))

    page_set.extend(slice_pages(current_page, slice_size))

    if current_page.number + slice_size < paginator.num_pages:
        if current_page.number + slice_size < paginator.num_pages - 2:
            page_set.append("...")
        elif current_page.number + slice_size < paginator.num_pages - 1:
            page_set.append(paginator.page(paginator.num_pages - 1))
        page_set.append(paginator.page(paginator.num_pages))

    return page_set
