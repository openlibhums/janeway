from django.core.management.base import BaseCommand

from utils import importer

from django.core.management import call_command


class Command(BaseCommand):
    """Takes a Ubiquity Press journal and lists articles in the backend."""

    help = "List articles in the backend of a Ubiquity Press journal."

    def add_arguments(self, parser):
        """Adds arguments to Django's management command-line parser.

        :param parser: the parser to which the required arguments will be added
        :return: None
        """
        parser.add_argument('journal_code')
        parser.add_argument('url')
        parser.add_argument('auth_file')

    def handle(self, *args, **options):
        """Imports a set of UP journal-level metadata into Janeway.

        :param args: None
        :param options: Dictionary containing 'url', 'journal_id', and a 'user_id'
        :return: None
        """
        users = importer.up.get_user_list(options.get("url"), options.get("auth_file"))

        for user in users:
            call_command('import_jms_user', options.get("journal_code"), options.get('url'), user,
                         options.get('auth_file'))
