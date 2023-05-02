from django.core.management.base import BaseCommand

from utils import models, logic


class Command(BaseCommand):
    """Attempts to update mailgun status for log entries"""

    help = "Attempts to update delivery status for mailgun emails."

    def add_arguments(self, parser):
        """Adds arguments to Django's management command-line parser.

        :param parser: the parser to which the required arguments will be added
        :return: None
        """
        parser.add_argument('log_id', type=int)

    def handle(self, *args, **options):
        log_id = options.get('log_id')
        log_entry = models.LogEntry.objects.get(pk=log_id)
        logic.send_bounce_notification_to_event_actor(log_entry)