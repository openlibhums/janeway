from django.core.management import call_command
from django.core.management.base import BaseCommand

from journal import models as journal_models
from core import models as core_models


class Command(BaseCommand):
    """ A management command to nuke the current DB."""

    help = "Nukes the current DB. Deletes all journals and settings. Dangerous."

    def handle(self, *args, **options):
        """ Deletes all current journals and reinstalls the press.

        :param args: None
        :param options: None.
        :return: None
        """

        journal_models.Journal.objects.all().delete()

        core_models.SettingValue.objects.all().delete()
        core_models.Setting.objects.all().delete()

        call_command('show_configured_journals')
