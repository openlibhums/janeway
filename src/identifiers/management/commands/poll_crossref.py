from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db.models import Q

from identifiers import models


class Command(BaseCommand):
    """
    Executes all of Janeway's cron tasks.
    """

    help = "Poll 20 Crossref tasks that need doing."

    def add_arguments(self, parser):
        parser.add_argument('tasks',
            default=20,
            type=int,
            nargs='?',
            help="The maximum number of tasks that will be run"
        )
        parser.add_argument('--journal_code',
            nargs='?',
            help="Filter tasks by journal"
        )

    def handle(self, *args, **options):
        """Polls all outstanding deposits.

        :param args: None
        :param options: None
        :return: None
        """
        print("Polling deposits.")
        outstanding_deposits = (Q(queued=True) | Q(has_result='False'))
        filter_args= [outstanding_deposits]
        filter_kwargs={}
        if options.get("journal_code"):
            filter_kwargs["identifier__article__journal__code"] = options["journal_code"]

        deposits = models.CrossrefDeposit.objects.filter(
                *filter_args, **filter_kwargs)[:options["tasks"]]

        if deposits.count() < 1:
            print("No deposits to handle")

        for deposit in deposits:
            print("Handling deposit {0}.xml".format(deposit.file_name))
            deposit.poll()

            if deposit.queued:
                print("[QUEUED]{}".format(deposit))
            elif deposit.success:
                print("[SUCCESS]{}".format(deposit))
            else:
                print("[FAILURE]{}".format(deposit))
                self.stderr.write("[FAILURE]{}".format(deposit))
