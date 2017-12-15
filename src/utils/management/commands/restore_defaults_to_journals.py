from django.core.management.base import BaseCommand

from journal import models as journal_models

from utils import install


class Command(BaseCommand):
    """A management command to synchronize all default settings to all journals."""

    help = "Synchronizes all default settings to all journals."

    def handle(self, *args, **options):
        """Synchronizes settings to journals.

        :param args: None
        :param options: None
        :return: None
        """

        journals = journal_models.Journal.objects.all()

        print("Journals:")
        for journal in journals:
            install.update_settings(journal, management_command=True, overwrite_with_defaults=True)
            print('Journal with ID {0} [{1}]: {2}. SETTINGS SYNCED.'.format(journal.id, journal.name, journal.domain))
