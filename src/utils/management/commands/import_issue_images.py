from django.core.management.base import BaseCommand

from utils import importer


class Command(BaseCommand):
    """Takes a Ubiquity Press journal and pulls in the issue cover images."""

    help = "Takes a Ubiquity Press journal and pulls in the issue cover images. Note: takes base URL without slash."

    def add_arguments(self, parser):
        """Adds arguments to Django's management command-line parser.

        :param parser: the parser to which the required arguments will be added
        :return: None
        """
        parser.add_argument('url')
        parser.add_argument('journal_id')
        parser.add_argument('user_id')

    def handle(self, *args, **options):
        """Imports a set of UP issue images into Janeway.

        :param args: None
        :param options: Dictionary containing 'url', 'journal_id', and a 'user_id'
        :return: None
        """
        importer.import_issue_images(**options)
