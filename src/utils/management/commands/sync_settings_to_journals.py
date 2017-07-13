import sys

from django.core.management.base import BaseCommand
from django.utils import translation

from journal import models as journal_models
from utils import install


class Command(BaseCommand):
    """A management command to synchronize all default settings to all journals."""

    help = "Synchronizes unspecified default settings to all journals."

    def add_arguments(self, parser):
        """ Adds arguments to Django's management command-line parser.

        :param parser: the parser to which the required arguments will be added
        :return: None
        """
        parser.add_argument('journal_code', nargs='?', default=None)

    def handle(self, *args, **options):
        """Synchronizes settings to journals.

        :param args: None
        :param options: None
        :return: None
        """

        translation.activate('en')
        journals = journal_models.Journal.objects.all()

        journal_code = options.get('journal_code', None)
        if journal_code:
            try:
                journals = [journal_models.Journal.objects.get(code=journal_code)]
            except journal_models.Journal.DoesNotExist:
                journals = None
                print('No journal with that code was found.')

        if journals:
            print("Syncing to {0} Journals:".format(len(journals)))
            for journal in journals:
                install.update_settings(journal, management_command=True)
                print('Journal with ID {0} [{1}]: {2}. SETTINGS SYNCED.'.format(journal.id, journal.name, journal.domain))
                install.update_license(journal, management_command=True)
