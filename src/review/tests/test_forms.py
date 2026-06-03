from django.test import TestCase

from review.forms import ReviewerNotificationForm
from utils.install import update_settings, update_xsl_files
from utils.testing import helpers
from journal import models as journal_models


class ReviewerNotificationFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        helpers.create_press()
        update_settings()
        update_xsl_files()
        cls.journal = journal_models.Journal(code="EANF", domain="eanf.testserver")
        cls.journal.save()
        update_settings(cls.journal, management_command=False)
        cls.editor = helpers.create_user(
            "eanf_editor@example.com", roles=["editor"], journal=cls.journal
        )
        cls.editor.is_active = True
        cls.editor.save()

    def _make_request(self):
        return helpers.get_request(
            user=self.editor,
            journal=self.journal,
            press=self.journal.press,
        )

    def _form(self, body, expected_url=None, button="confirmable"):
        request = self._make_request()
        data = {
            "cc": "",
            "bcc": "",
            "subject": "Test",
            "body": body,
            button: button,
        }
        return ReviewerNotificationForm(
            data,
            setting_name="review_assignment",
            email_context={
                "article": None,
                "editor": self.editor,
                "review_assignment": None,
                "review_url": "http://example.com/review/requests/1/?access_code=abc",
                "article_details": "",
            },
            expected_url=expected_url,
            request=request,
        )

    def test_no_expected_url_no_potential_errors(self):
        form = self._form(body="No URL here at all.", expected_url=None)
        form.is_valid()
        self.assertEqual(form.check_for_potential_errors(), [])

    def test_url_present_in_body_no_potential_errors(self):
        expected_url = "http://example.com/review/requests/1/?access_code=abc"
        form = self._form(
            body="Please visit: {}".format(expected_url),
            expected_url=expected_url,
        )
        form.is_valid()
        self.assertEqual(form.check_for_potential_errors(), [])

    def test_url_missing_from_body_returns_error(self):
        expected_url = "http://example.com/review/requests/1/?access_code=abc"
        form = self._form(body="No link here.", expected_url=expected_url)
        form.is_valid()
        errors = form.check_for_potential_errors()
        self.assertEqual(len(errors), 1)
        self.assertIn(expected_url, errors[0])

    def test_url_missing_creates_modal_on_confirmable_submit(self):
        expected_url = "http://example.com/review/requests/1/?access_code=abc"
        form = self._form(
            body="No link here.",
            expected_url=expected_url,
            button="confirmable",
        )
        form.is_valid()
        self.assertIsNotNone(form.modal)

    def test_url_present_no_modal_on_confirmable_submit(self):
        expected_url = "http://example.com/review/requests/1/?access_code=abc"
        form = self._form(
            body="Please visit: {}".format(expected_url),
            expected_url=expected_url,
            button="confirmable",
        )
        form.is_valid()
        self.assertIsNone(form.modal)

    def test_is_confirmed_true_when_url_present(self):
        expected_url = "http://example.com/review/requests/1/?access_code=abc"
        form = self._form(
            body="Please visit: {}".format(expected_url),
            expected_url=expected_url,
            button="confirmable",
        )
        form.is_valid()
        self.assertTrue(form.is_confirmed())

    def test_is_confirmed_false_when_url_missing_and_not_confirmed(self):
        expected_url = "http://example.com/review/requests/1/?access_code=abc"
        form = self._form(
            body="No link here.",
            expected_url=expected_url,
            button="confirmable",
        )
        form.is_valid()
        self.assertFalse(form.is_confirmed())

    def test_is_confirmed_true_when_confirmed_button_used(self):
        expected_url = "http://example.com/review/requests/1/?access_code=abc"
        form = self._form(
            body="No link here.",
            expected_url=expected_url,
            button="confirmed",
        )
        form.is_valid()
        self.assertTrue(form.is_confirmed())
