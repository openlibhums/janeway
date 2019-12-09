import time

from django.core.management.base import BaseCommand

from journal import models as journal_models
from press import models as press_models


class Command(BaseCommand):
    """A management command to alter journal/press domains."""

    help = "Allows users to alter journal/press domains"

    def add_arguments(self, parser):
        """ Adds arguments to Django's management command-line parser.

        :param parser: the parser to which the required arguments will be added
        :return: None
        """
        parser.add_argument('journal_code', nargs='?', default=None)

    def handle(self, *args, **options):
        """Allows users to alter journal/press domains"

        :param args: None
        :param options: None
        :return: None
        """
        journal = None
        press = press_models.Press.objects.all()[0]
        journal_code = options.get('journal_code', None)

        if journal_code:
            if journal_code == 'press':
                journal = press
            else:
                try:
                    journal = journal_models.Journal.objects.get(code=journal_code)
                except journal_models.Journal.DoesNotExist:
                    print('No journal with that code found.')

        if not journal_code:
            journals = journal_models.Journal.objects.all()

            while True:
                for journal in journals:
                    print('Code: {code} - {name}'.format(code=journal.code, name=journal.name))

                print('Code: press - {press_name}'.format(press_name=press.name))
                journal_code = input('Please select a journal to edit, enter the ID number: ')
                try:
                    if journal_code == 'press':
                        journal = press
                        break
                    journal = journals.get(code=journal_code)
                    break
                except journal_models.Journal.DoesNotExist:
                    print('No journal with that code found.')
                    time.sleep(2)

        print('Altering domain for {journal}, current domain: {domain}'.format(journal=journal.name, domain=journal.domain))
        new_domain = input('Enter the new domain you wish to set: ')

        print('Altering domain record...', end='')
        journal.domain = new_domain
        journal.save()
        print('... [Ok]')
