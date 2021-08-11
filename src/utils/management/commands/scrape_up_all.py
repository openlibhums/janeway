from django.core.management.base import BaseCommand

from utils import importer


class Command(BaseCommand):
    """ Takes a Ubiquity Press url and imports it into Janeway."""

    help = "Takes an UP url and pulls information into Janeway."

    def add_arguments(self, parser):
        """Adds arguments to Django's management command-line parser.

        :param parser: the parser to which the required arguments will be added
        :return: None
        """
        parser.add_argument('url')
        parser.add_argument('journal_code')
        parser.add_argument('user_id')
        parser.add_argument(
            '--delete',
            action='store_true',
            dest='delete',
            default=1,
            help='Delete all articles and non-superusers in the database '
                'before import',
        )
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
        importer.import_all(**options)

