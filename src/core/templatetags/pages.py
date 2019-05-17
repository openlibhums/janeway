"""
Template tags for handling paginator objects
"""
from django import template

register = template.Library()


@register.filter()
def slice_pages(current_page, slice_size=2):
    """ Given a page and a slice size returns a slice of pages

    :current_page: A django.core.paginator.Page
    :slice_size: int
    """
    paginator = current_page.paginator
    slice_size = int(slice_size)
    first = max(1, current_page.number - slice_size)
    last = min(paginator.num_pages, current_page.number + slice_size)
    return [
        current_page.paginator.page(page_num)
        for page_num in range(first, last + 1)
    ]
