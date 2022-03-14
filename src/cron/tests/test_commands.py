from django.test import TestCase
from django.core.management import call_command
from utils.testing import helpers
from cron.management.commands import send_reminders
from cron import forms, models
from django.utils import timezone

class SendRemindersCommandTests(TestCase):
    """
    Unit tests for commands.
    """
    @classmethod
    def setUpTestData(cls):

        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.review_assignment = helpers.create_review_assignment(journal=cls.journal_one)
        cls.review_reminder = helpers.create_reminder(
            journal=cls.journal_one,
            reminder_type='review'
        )

    def test_handle(self):
        call_command('send_reminders')
        reminder_item = self.review_reminder.items_for_reminder()[0]
        sent_check = models.SentReminder.objects.filter(
            type=self.review_reminder.type,
            object_id=reminder_item.pk,
            sent=timezone.now().date(),
        )
        self.assertTrue(sent_check)
