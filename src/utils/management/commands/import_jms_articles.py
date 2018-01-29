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
        parser.add_argument('article_type')
        parser.add_argument('auth_file')

    def handle(self, *args, **options):
        """Imports a set of UP journal-level metadata into Janeway.

        :param args: None
        :param options: Dictionary containing 'url', 'journal_id', and a 'user_id'
        :return: None
        """
        articles = importer.up.get_article_list(options.get("url"), options.get("article_type"),
                                                options.get("auth_file"))

        for article in articles:

            if options.get("article_type") == 'in_review':
                call_command('up_import_review_article', options.get("journal_code"), options.get('url'), article,
                             options.get('auth_file'))

            if options.get('article_type') == 'in_editing':
                call_command('up_import_editing_article', options.get("journal_code"), options.get('url'), article,
                             options.get('auth_file'))
