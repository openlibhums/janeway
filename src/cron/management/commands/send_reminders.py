from django.core.management.base import BaseCommand

from cron import models
from journal import models as journal_models


class Command(BaseCommand):
    """
    A management command that pulls and sends all required reminders
    """

    help = "Sends review and revision reminder emails.."

    def handle(self, *args, **options):

        journals = journal_models.Journal.objects.all()

        for journal in journals:
            print("Processing reminders for journal {0}: {1}".format(journal.pk, journal.name))

            reminders = models.Reminder.objects.filter(journal=journal)

            for reminder in reminders:
                print("Reminder {0}, target date: {1}".format(reminder, reminder.target_date()))
                reminder.send_reminder()
