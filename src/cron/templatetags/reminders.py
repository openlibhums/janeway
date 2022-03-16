from django import template

from cron import models

register = template.Library()


@register.simple_tag()
def check_reminder_sent(review_assignment, reminder):
    check = models.SentReminder.objects.filter(
        type
        object_id=review_assignment.pk,
        reminder=reminder,
        sent__isnull=False,
    ).exists()