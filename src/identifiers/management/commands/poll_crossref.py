from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db.models import Q

from identifiers import models
from utils.logger import get_logger

logger = get_logger(__name__)

MAX_POLLING_ATTEMPTS = 20

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
        parser.add_argument('attempts',
            default=MAX_POLLING_ATTEMPTS,
            type=int,
            nargs='?',
            help="The maximum number of attempts to poll a single deposit"
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
        outstanding_deposits = (Q(queued=True) | Q(has_result=False))
        filter_args= [outstanding_deposits]
        filter_kwargs={}
        if options.get("journal_code"):
            filter_kwargs["identifier__article__journal__code"] = options["journal_code"]
        if options.get("attempts") > 0:
            filter_kwargs["polling_attempts__lte"] = options["attempts"]

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

            # Update existing CrossrefStatus objects.
            # Assumes that if a deposit exists, a status exists
            # for each identifier in the deposit batch.
            for status in models.CrossrefStatus.objects.filter(
                deposits=deposit
            ):
                status.update()

        stale_attempts = models.CrossrefDeposit.objects.filter(
                polling_attempts__gt=MAX_POLLING_ATTEMPTS,
                success=False,
        )
        if stale_attempts:
            logger.warning(
                "Found {0} deposits with more than {1} poll attempts".format(
                   stale_attempts.count(), MAX_POLLING_ATTEMPTS,
                )
            )
