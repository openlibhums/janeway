__copyright__ = "Copyright 2026 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.translation import get_language_info

from utils import setting_handler
from utils.shared import clear_cache
from utils.testing import helpers


class LanguageInfoTests(TestCase):
    def test_every_configured_language_keeps_its_own_code(self):
        codes = [get_language_info(code)["code"] for code, _ in settings.LANGUAGES]
        self.assertEqual(codes, [code for code, _ in settings.LANGUAGES])

    def test_en_us_is_not_reported_as_en(self):
        info = get_language_info("en-us")
        self.assertEqual(info["code"], "en-us")
        self.assertEqual(info["name_local"], "English (US)")


@override_settings(URL_CONFIG="domain")
class LanguageSwitcherDuplicateTests(TestCase):
    """English was listed twice in the language switchers (#5672)."""

    THEMES = ("OLH", "material", "clean", "clarity")

    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        helpers.set_journal_languages(
            cls.journal_one,
            available=["en", "fr", "de"],
            default="en",
        )
        setting_handler.save_setting(
            "general", "switch_language", cls.journal_one, True
        )

    def get_home(self, theme):
        setting_handler.save_setting(
            "general", "journal_theme", self.journal_one, theme
        )
        clear_cache()
        response = self.client.get(
            reverse("website_index"),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(response.status_code, 200)
        return response.content.decode()

    def test_each_language_is_offered_once(self):
        for theme in self.THEMES:
            with self.subTest(theme=theme):
                content = self.get_home(theme)
                for code in ("en", "fr", "de"):
                    self.assertEqual(
                        content.count('value="{}"'.format(code)),
                        1,
                        (theme, code),
                    )
                self.assertNotIn('value="en-us"', content)
