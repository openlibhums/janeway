from django import template
from django.utils import timezone


register = template.Library()

@register.simple_tag
def due_date(days=0, input_type="date"):
    """
    Get a string representing today's date or the now datetime,
    with an offset of X days.
    """
    due = timezone.now() + timezone.timedelta(days=days)
    if input_type == "date":
        return due.strftime("%Y-%m-%d")
    elif input_type == "datetime-local":
        return due.strftime("%Y-%m-%dT%H:%M")
