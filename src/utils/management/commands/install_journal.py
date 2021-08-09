from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.utils import translation

from journal import models as journal_models
import utils.install as install

class Command(BaseCommand):
    """ A management command to install a new journal."""

    help = "Installs a journal."

    def add_arguments(self, parser):
        """ Adds arguments to Django's management command-line parser.

        :param parser: the parser to which the required arguments will be added
        :return: None
        """
        parser.add_argument('--journal_name', default=False)
        parser.add_argument('--journal_code', default=False)
        parser.add_argument('--base_url', default=False)
        parser.add_argument('--delete', action='store_true', default=False)

    def handle(self, *args, **options):
        """ Create a new journal on this Janeway install.

        :param args: None
        :param options: Dictionary containing keys '--journal_name', '--journal_code' and '--base_url'. If any of these
        are not provided, they will be requested via raw_input. --delete can be provided to find and delete the journal
        if it already exists.
        :return: None
        """

        translation.activate('en')
        delete = True if options.get('delete') else False
        journal_name = options.get('journal_name') if options.get('journal_name') else input(
            'Enter the full name of the Journal: ')
        journal_code = options.get('journal_code') if options.get('journal_code') else input(
            'Enter a short name for the Journal: ')
        base_url = options.get('base_url') if options.get('base_url') else input(
            'Enter a base url for the Journal: ')

        if journal_name and journal_code and base_url:
            print('Creating new journal {0} ({1}) with domain {2}.'.format(journal_name, journal_code, base_url))

            install.journal(name=journal_name, code=journal_code, base_url=base_url, delete=delete)

            if not delete:
                journal = journal_models.Journal.objects.get(code=journal_code)
                install.update_issue_types(journal, management_command=False)

            call_command('show_configured_journals')
