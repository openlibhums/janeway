from django.test import TestCase

from journal.tests.utils import make_test_journal
from repository.forms import RepositoryInitial
from utils.testing import helpers


class RepositoryInitialFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()

    def _data(self, short_name):
        return {
            "name": "Test Repository",
            "short_name": short_name,
            "domain": "",
            "object_name": "Preprint",
            "object_name_plural": "Preprints",
            "theme": "OLH",
            "publisher": "Test Publisher",
        }

    def test_reserved_short_name_rejected_with_message_and_suggestion(self):
        form = RepositoryInitial(data=self._data("cms"), press=self.press)
        self.assertFalse(form.is_valid())
        message = form.errors["short_name"][0]
        self.assertIn("built-in Janeway system page", message)
        self.assertIn("Try '", message)

    def test_valid_short_name_accepted(self):
        form = RepositoryInitial(data=self._data("myrepo"), press=self.press)
        self.assertTrue(form.is_valid())

    def test_short_name_matching_existing_repository_rejected(self):
        existing, _ = helpers.create_repository(self.press, [], [])
        form = RepositoryInitial(data=self._data(existing.short_name), press=self.press)
        self.assertFalse(form.is_valid())
        message = form.errors["short_name"][0]
        self.assertIn("already in use by another repository", message)
        self.assertIn("Try '", message)

    def test_short_name_matching_existing_journal_code_rejected(self):
        journal = make_test_journal(code="jform", domain="jform.example.org")
        form = RepositoryInitial(data=self._data(journal.code), press=self.press)
        self.assertFalse(form.is_valid())
        message = form.errors["short_name"][0]
        self.assertIn("already in use by a journal", message)
