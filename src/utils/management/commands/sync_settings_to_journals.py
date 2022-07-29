import json
import os

from django.core.management.base import BaseCommand
from django.utils import translation
from django.conf import settings

from journal import models as journal_models
from press import models as press_models
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

        #We don't need this now that we have a default for the settings
        self.stderr.write("Command deprecated on Janeway > v1.3.3.1")
        return

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

        if not journal_code:
            file = open(os.path.join(settings.BASE_DIR, 'utils', 'install', 'press_settings.json'), 'r')
            text = json.loads(file.read())

            for setting in text:
                for press in press_models.Press.objects.all():
                    print("Syncing to {press}".format(press=press.name))
                    setting = press_models.PressSetting.objects.get_or_create(press=press,
                                                                              name=setting['name'],
                                                                              defaults={
                                                                                  'value': setting['value'],
                                                                                  'is_boolean': setting['is_boolean']
                                                                              })
