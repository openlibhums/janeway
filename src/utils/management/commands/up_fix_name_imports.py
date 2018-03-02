from django.core.management.base import BaseCommand
from django.utils import translation
from django.db.models import Q

from submission import models as models
from utils import shared


class Command(BaseCommand):
    """
    Loops through anomalous fronzen author records and helps you fix them.
    """

    help = "Installs a press and oe journal for Janeway."

    def handle(self, *args, **options):
        """Loops through anomalous fronzen author records and helps you fix them.

        :param args: None
        :param options: None
        :return: None
        """
        print("This function will search for author and frozen author names with anomalies and allow you to "
              "fix them.\n")
        translation.activate('en')

        anomaly = input('Insert anomaly to seach for, this will use an i_contains search: ')

        print('Searching Account records... ', end='')

        accounts = models.FrozenAuthor.objects.filter(
            Q(first_name__icontains=anomaly) |
            Q(middle_name__icontains=anomaly) |
            Q(last_name__icontains=anomaly)
        )

        print('[ok]')
        print('Looking through Author objects.')

        for account in accounts:

            print('Updating {full_name} - {email}'.format(full_name=account.full_name(),
                                                          email=account.author.email))

            first_update, middle_update, last_update = False, False, False

            if anomaly in account.first_name:
                print('Anomaly detected in first name')
                if not account.first_name == account.author.first_name:
                    first_update = shared.yes_or_no('Update from the author record ({author_fname})'.format(
                        author_fname=account.author.first_name))
                if not first_update:
                    first_update = input('Insert new first name: ')

            if anomaly in account.middle_name:
                print('Anomaly detected in middle name')
                if not account.middle_name == account.author.middle_name:
                    middle_update = shared.yes_or_no('Update from the author record ({author_mname})'.format(
                        author_mname=account.author.middle_name))
                    if middle_update:
                        middle_update = account.author.middle_name if account.author.middle_name else ''
                if not middle_update == '' and not middle_update:
                    middle_update = input('Insert new middle name: ')

            if anomaly in account.last_name:
                print('Anomaly detected in last name')
                if not account.last_name == account.author.last_name:
                    last_update = shared.yes_or_no('Update from the author record ({author_lname})'.format(
                        author_lname=account.author.last_name))
                if not last_update:
                    last_update = input('Insert new last name: ')

            if first_update:
                account.first_name = first_update

            if middle_update == '' or middle_update:
                account.middle_name = middle_update

            if last_update:
                account.last_name = last_update

            account.save()
