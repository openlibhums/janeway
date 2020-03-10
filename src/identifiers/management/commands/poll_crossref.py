from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db.models import Q

from identifiers import models


class Command(BaseCommand):
    """
    Executes all of Janeway's cron tasks.
    """

    help = "Poll 20 Crossref tasks that need doing."

    def handle(self, *args, **options):
        """Polls all outstanding deposits.

        :param args: None
        :param options: None
        :return: None
        """
        print("Polling deposits.")
        ids = models.CrossrefDeposit.objects.filter(Q(queued=True) | Q(has_result='False'))

        if len(ids) > 0:
            deposits = ids[0:20]
        else:
            print("No deposits to handle")
            deposits = []

        for deposit in deposits:
            print("Handling deposit {0}.xml".format(deposit.file_name))
            deposit.poll()
