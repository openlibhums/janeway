from django.core.management.base import BaseCommand

from core import models
from cron import logic
from journal import models as journal_models


class Command(BaseCommand):
    """
    A management command that sends digest emails.
    """

    help = "Sends digest emails"

    def handle(self, *args, **options):

        journals = journal_models.Journal.objects.all()

        for journal in journals:
            print("Processing journal {0} - {1}".format(journal.pk, journal.code))

            users = models.Account.objects.filter(enable_digest=True)

            for user in users:
                print("Processing user {0}".format(user.full_name()))
                user_roles = models.AccountRole.objects.filter(user=user, journal=journal)

                text = ''
                for user_role in user_roles:
                    print("Processing role {0}".format(user_role.role.name))

                    items = logic.process_digest_items(journal, user_role)
                    if items:
                        text = text + '\n\n' + items

                print(text)
                print("-------------------------------------------")
