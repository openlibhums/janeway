from django.core.management.base import BaseCommand
from django.core.management import call_command

from cron import models
from utils.logger import get_logger

logger = get_logger(__name__)


class Command(BaseCommand):
    """
    Executes all of Janeway's cron tasks.
    """

    help = "Executes all of Janeway's cron tasks."

    def handle(self, *args, **options):
        """Executes all of Janeway's cron tasks.

        :param args: None
        :param options: None
        :return: None
        """
        print("Executing cron tasks now.")
        call_command("send_digest_emails")
        call_command("send_reminders")
        call_command("poll_crossref")
        # Requests for a copy nobody answered in time: tell the readers.
        try:
            call_command("expire_copy_requests")
        except Exception:
            # A failure here mustn't stop the tasks below.
            logger.exception("expire_copy_requests failed")
        call_command("clearsessions")
        models.CronTask.run_tasks()
