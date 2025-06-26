from datetime import timedelta

import pytz
from django import template
from django.utils import timezone



register = template.Library()

@register.simple_tag(takes_context=True)
def offset_date(context, days=0, input_type="date"):
    """
    Get a string representing today's date or the now datetime,
    with an offset of X days.
    :param context: template context, needed to access request.user
    :param days: number of days from now that the date should be set
    :param input_type: date or datetime-local

    Usage:

    <input
      id="due"
      name="due"
      type="{{ input_type }}"
      value="{% offset_date days=3 input_type=input_type %}">

    See admin.core.widgets.soon_date_buttons for a use case.
    """
    request = context.get("request", None)
    now = timezone.now()

    if request and hasattr(request, "user"):
        tz_name = request.user.preferred_timezone  # always present, may be ''
        if tz_name:
            try:
                tz = pytz.timezone(tz_name)
                if timezone.is_naive(now):
                    now = timezone.make_aware(now, timezone=tz)
                else:
                    now = now.astimezone(tz)
            except pytz.UnknownTimeZoneError:
                pass

    due = now + timedelta(days=days)

    if input_type == "date":
        return due.strftime("%Y-%m-%d")
    elif input_type == "datetime-local":
        return due.strftime("%Y-%m-%dT%H:%M")
