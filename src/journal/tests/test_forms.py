from django.test import TestCase

from journal.forms import JournalForm
from utils.testing import helpers


class JournalFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()

    def test_reserved_code_rejected_with_message_and_suggestion(self):
        form = JournalForm(data={"code": "cms", "domain": ""})
        self.assertFalse(form.is_valid())
        message = form.errors["code"][0]
        self.assertIn("built-in Janeway system page", message)
        self.assertIn("Try '", message)

    def test_valid_code_accepted(self):
        form = JournalForm(data={"code": "myjournal", "domain": ""})
        self.assertTrue(form.is_valid())

    def test_duplicate_code_rejected_with_message_and_suggestion(self):
        journal_one, _ = helpers.create_journals()
        form = JournalForm(data={"code": journal_one.code, "domain": ""})
        self.assertFalse(form.is_valid())
        message = form.errors["code"][0]
        self.assertIn("already in use by another journal", message)
        self.assertIn("Try '", message)

    def test_code_matching_existing_repository_short_name_rejected(self):
        repository, _ = helpers.create_repository(self.press, [], [])
        form = JournalForm(data={"code": repository.short_name, "domain": ""})
        self.assertFalse(form.is_valid())
        message = form.errors["code"][0]
        self.assertIn("already in use by a repository", message)
