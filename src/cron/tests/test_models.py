from django.test import TestCase
from django.core.management import call_command
from utils.testing import helpers
from cron import forms, models

class ModelTests(TestCase):
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
            reminder_type='review',
        )
        cls.review_assignment = helpers.create_review_assignment(journal=cls.journal_two)

    def test_items_for_reminder(self):
        self.assertEqual(1, len(self.review_reminder.items_for_reminder()))
