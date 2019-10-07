from django.core.management.base import BaseCommand
from django.utils import translation

from utils import importer


class Command(BaseCommand):
    """Takes an OAI PMH url and pulls information into Janeway."""

    help = "Takes an OAI PMH url and pulls information into Janeway."

    def add_arguments(self, parser):
        """Adds arguments to Django's management command-line parser.

        :param parser: the parser to which the required arguments will be added
        :return: None
        """
        parser.add_argument('url')
        parser.add_argument('journal_id')
        parser.add_argument('user_id')
        parser.add_argument('-u', '--update',
                            action='store_true',
                            dest='update',
                            default=False,
                            help='Updates metadata if the item already exists')
        parser.add_argument('--delete',
                            action='store_true',
                            dest='delete',
                            default=False,
                            help='Delete all articles and non-superusers in the database before import')

    def handle(self, *args, **options):
        """Imports an OAI feed into Janeway.

        :param args: None
        :param options: Dictionary containing 'url', 'journal_id', 'user_id', and a boolean '--delete' flag
        :return: None
        """
        translation.activate('en')
        importer.import_oai(**options)
