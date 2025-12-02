from django import template
import threading

register = template.Library()

_counter = threading.local()


def _get_counter():
    if not hasattr(_counter, "value"):
        _counter.value = 0
    return _counter


@register.simple_tag
def get_next_id(prefix="id"):
    """
    Returns an incrementing id value unique within a single request/thread.
    Primiarily for use within templates to create unique element ID
    for use with aria references.
    """
    counter = _get_counter()
    counter.value += 1
    return f"{prefix}-{counter.value}"
