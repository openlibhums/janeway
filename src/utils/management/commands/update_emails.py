from django.core.management.base import BaseCommand
from django.utils import translation

from journal import models as journal_models
from utils import install


class Command(BaseCommand):
    """A management command to updates all default email settings to all journals."""

    help = "Synchronizes unspecified default settings to all journals."

    def add_arguments(self, parser):
        """ Adds arguments to Django's management command-line parser.

        :param parser: the parser to which the required arguments will be added
        :return: None
        """
        parser.add_argument('journal_code', nargs='?', default=None)

    def handle(self, *args, **options):
        """Updates email settings for journals.

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
            print("Updated emails for {0} Journals:".format(len(journals)))
            for journal in journals:
                print("Updating journal {0}".format(journal.name))
                install.update_emails(journal, management_command=True)
