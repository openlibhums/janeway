from django.test import TestCase
from django.core.management import call_command
from utils.testing import helpers
from cron.management.commands import send_reminders
from cron import forms, models
from django.utils import timezone
from submission import models as submission_models


class SendRemindersCommandTests(TestCase):
    """
    Unit tests for commands.
    """

    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.review_assignment = helpers.create_review_assignment(
            journal=cls.journal_one
        )
        cls.author = helpers.create_author(cls.journal_one)
        cls.editor = helpers.create_editor(cls.journal_one)
        cls.article_under_review = helpers.create_article(
            journal=cls.journal_one,
            title="A Test Article",
            owner=cls.author,
            correspondence_author=cls.author,
            abstract="An abstract",
            stage=submission_models.STAGE_UNDER_REVIEW,
        )
        cls.review_reminder = helpers.create_reminder(
            journal=cls.journal_one, reminder_type="review"
        )
        cls.revision_request = helpers.create_revision_request(
            article=cls.article_under_review,
            editor=cls.editor,
        )
        cls.revision_reminder = helpers.create_reminder(
            journal=cls.journal_one, reminder_type="revisions"
        )

    def test_handle_review(self):
        call_command("send_reminders")
        reminder_item = self.review_reminder.items_for_reminder()[0]
        sent_check = models.SentReminder.objects.filter(
            type=self.review_reminder.type,
            object_id=reminder_item.pk,
            sent=timezone.now().date(),
        )
        self.assertTrue(sent_check)

    def test_handle_revision_request(self):
        call_command("send_reminders")
        reminder_item = self.revision_reminder.items_for_reminder()[0]
        sent_check = models.SentReminder.objects.filter(
            type=self.revision_reminder.type,
            object_id=reminder_item.pk,
            sent=timezone.now().date(),
        )
        self.assertTrue(sent_check)
