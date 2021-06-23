from django.core.management.base import BaseCommand

from core.models import Account
from journal.models import Journal
from utils import importer
from utils.importers import up


class Command(BaseCommand):
    """ Takes a UP journal and imports its collections into Janeway."""

    help = "Takes an UP url and pulls collections nto Janeway."

    def add_arguments(self, parser):
        """Adds arguments to Django's management command-line parser.

        :param parser: the parser to which the required arguments will be added
        :return: None
        """
        parser.add_argument('url')
        parser.add_argument('journal_code')
        parser.add_argument('user_id')
        parser.add_argument('-u', '--update',
                            action='store_true',
                            dest='update',
                            default=False,
                            help='Updates metadata if the item already exists',
        )

    def handle(self, *args, **options):
        """Imports a Ubiquity Press article into Janeway.

        :param args: None
        :param options: Dictionary containing 'url', 'journal_id', 'user_id', and a boolean '--delete' flag
        :return: None
        """
        journal = Journal.objects.get(code=options["journal_code"])
        owner = Account.objects.get(pk=options["user_id"])
        update = options["update"]
        up.import_collections(journal, options["url"], owner, update=update)

