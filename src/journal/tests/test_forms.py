from bs4 import BeautifulSoup
from django.template import Context, Template
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

    def test_invalid_form_renders_accessible_error_association(self):
        form = JournalForm(data={"code": "cms", "domain": ""})
        form.is_valid()
        html = Template("{% load foundation %}{{ form|foundation }}").render(
            Context({"form": form})
        )
        soup = BeautifulSoup(html, "html.parser")
        error = soup.find(id="id_code_error_1")
        code_input = soup.find(id="id_code")
        self.assertIsNotNone(error)
        self.assertIsNotNone(code_input)
        self.assertIn("id_code_error_1", code_input["aria-describedby"].split())

    def test_invalid_form_with_multiple_errors_gets_unique_ids(self):
        # A field can accumulate more than one error (e.g. model.clean()
        # plus a manually added error). Each must get its own id, and
        # aria-describedby must reference all of them.
        form = JournalForm(data={"code": "cms", "domain": ""})
        form.is_valid()
        form.add_error("code", "A second, unrelated error")
        html = Template("{% load foundation %}{{ form|foundation }}").render(
            Context({"form": form})
        )
        soup = BeautifulSoup(html, "html.parser")
        errors = soup.find_all(id=["id_code_error_1", "id_code_error_2"])
        self.assertEqual(len(errors), 2)
        code_input = soup.find(id="id_code")
        describedby_ids = code_input["aria-describedby"].split()
        self.assertIn("id_code_error_1", describedby_ids)
        self.assertIn("id_code_error_2", describedby_ids)
