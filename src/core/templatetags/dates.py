from datetime import datetime, timedelta

import pytz
from django import template
from django.conf import settings
from django.template.exceptions import TemplateSyntaxError
from django.utils import timezone, formats
from django.utils.translation import gettext as _
import logging

register = template.Library()
logger = logging.getLogger(__name__)


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


@register.filter(name="date_human", is_safe=True)
def date_human(value):
    """Convert a date to a human readable Day Month(text) Year format e.g. 3 January 2025"""
    if isinstance(value, datetime):
        return formats.date_format(
            value,
            format="j F Y",
            use_l10n=True,
        )
    else:
        error_message = (
            "The value filtered by `date_human` must be a `datetime.datetime`"
        )
        if settings.DEBUG:
            raise TemplateSyntaxError(error_message)
        else:
            logger.error(error_message)
            return ""
