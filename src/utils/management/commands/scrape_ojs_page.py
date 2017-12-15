from django.core.management.base import BaseCommand

from utils import importer


class Command(BaseCommand):
    """ Takes an OJS url and imports it into Janeway."""

    help = "Takes an OJS url and pulls information into Janeway."

    def add_arguments(self, parser):
        """Adds arguments to Django's management command-line parser.

        :param parser: the parser to which the required arguments will be added
        :return: None
        """
        parser.add_argument('url')
        parser.add_argument('journal_id')
        parser.add_argument('user_id')
        parser.add_argument('--delete',
                            action='store_true',
                            dest='delete',
                            default=False,
                            help='Delete all articles and non-superusers in the database before import')

    def handle(self, *args, **options):
        """Imports an OJS article into Janeway.

        :param args: None
        :param options: Dictionary containing 'url', 'journal_id', 'user_id', and a boolean '--delete' flag
        :return: None
        """
        importer.import_ojs_article(**options)
