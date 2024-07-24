from django import template
from django.utils import timezone


register = template.Library()

@register.simple_tag
def offset_date(days=0, input_type="date"):
    """
    Get a string representing today's date or the now datetime,
    with an offset of X days.
    :param days: number of days from now that the date should be set
    :param date: date or datetime-local

    Usage:

    <input
      id="due"
      name="due"
      type="{{ input_type }}"
      value="{% offset_date days=3 input_type=input_type %}">

    See admin.core.widgets.soon_date_buttons for a use case.

    """
    due = timezone.now() + timezone.timedelta(days=days)
    if input_type == "date":
        return due.strftime("%Y-%m-%d")
    elif input_type == "datetime-local":
        return due.strftime("%Y-%m-%dT%H:%M")
