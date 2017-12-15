from django.core.management.base import BaseCommand

from utils import importer


class Command(BaseCommand):
    """Takes a Ubiquity Press journal and lists articles in the backend."""

    help = "List articles in the backend of a Ubiquity Press journal."

    def add_arguments(self, parser):
        """Adds arguments to Django's management command-line parser.

        :param parser: the parser to which the required arguments will be added
        :return: None
        """
        parser.add_argument('url')
        parser.add_argument('auth_file')

    def handle(self, *args, **options):
        """Imports a set of UP journal-level metadata into Janeway.

        :param args: None
        :param options: Dictionary containing 'url', 'journal_id', and a 'user_id'
        :return: None
        """
        print(importer.up.get_user_list(options.get("url"), options.get("auth_file")))
