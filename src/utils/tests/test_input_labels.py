__copyright__ = "Copyright 2026 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from utils import setting_handler
from utils.forms import CaptchaForm
from utils.shared import clear_cache
from utils.testing import helpers


@override_settings(CAPTCHA_TYPE="simple_math")
class MathCaptchaLabelTests(SimpleTestCase):
    def test_label_targets_answer_input(self):
        field = CaptchaForm()["captcha"]
        self.assertEqual(field.id_for_label, "id_captcha")
        self.assertIn('for="id_captcha"', field.label_tag())
        self.assertIn('name="captcha_0"', str(field))
        self.assertIn('id="id_captcha"', str(field))

    def test_answer_input_is_described_by_question(self):
        html = str(CaptchaForm()["captcha"])
        self.assertIn('id="id_captcha_question"', html)
        self.assertIn('aria-describedby="id_captcha_question"', html)


@override_settings(URL_CONFIG="domain", CAPTCHA_TYPE="simple_math")
class InputLabelRequestTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.contact = helpers.create_user(
            "input_labels_contact@example.org",
            journal=cls.journal_one,
        )
        helpers.create_contact_person(cls.contact, cls.journal_one)
        setting_handler.save_setting(
            "general",
            "journal_theme",
            cls.journal_two,
            "clean",
        )

    def setUp(self):
        clear_cache()

    def test_contact_page_labels_captcha_answer(self):
        response = self.client.get(
            reverse("contact"),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertContains(response, 'for="id_captcha"')
        self.assertContains(
            response, 'name="captcha_0" size="5" required id="id_captcha"'
        )
        self.assertContains(response, 'aria-describedby="id_captcha_question"')

    def test_clean_articles_labels_paginate_by_select(self):
        response = self.client.get(
            reverse("journal_articles"),
            SERVER_NAME=self.journal_two.domain,
        )
        self.assertContains(response, 'id="paginate_by"')
        self.assertContains(response, 'for="paginate_by"')
        self.assertNotContains(response, "labelfor=")
