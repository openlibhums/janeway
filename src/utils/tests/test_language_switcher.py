__copyright__ = "Copyright 2026 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from unittest import mock

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.translation import get_language_info

from core.templatetags import translations
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


@override_settings(URL_CONFIG="domain")
class LanguageFlagTests(TestCase):
    """OLH falls back to a text button for a language with no flag image."""

    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        helpers.set_journal_languages(
            cls.journal_one,
            available=["en", "en-us", "es"],
            default="en",
        )
        setting_handler.save_setting(
            "general", "switch_language", cls.journal_one, True
        )
        setting_handler.save_setting("general", "journal_theme", cls.journal_one, "OLH")

    def setUp(self):
        clear_cache()
        translations._language_flag.cache_clear()
        self.addCleanup(translations._language_flag.cache_clear)

    def get_home(self):
        response = self.client.get(
            reverse("website_index"),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(response.status_code, 200)
        return response.content.decode()

    def test_every_configured_language_has_a_flag(self):
        for code, _ in settings.LANGUAGES:
            with self.subTest(code=code):
                self.assertTrue(translations.language_flag(code))

    def test_unknown_language_has_no_flag(self):
        self.assertEqual(translations.language_flag("xx"), "")

    def test_olh_shows_flags(self):
        content = self.get_home()
        for code in ("en", "en-us", "es"):
            self.assertIn("common/img/flags/{}.png".format(code), content)

    def test_olh_falls_back_to_text_without_a_flag(self):
        real_find = translations.finders.find

        def find(path, *args, **kwargs):
            if path.endswith("/es.png"):
                return None
            return real_find(path, *args, **kwargs)

        with mock.patch.object(translations.finders, "find", side_effect=find):
            content = self.get_home()
        self.assertNotIn("common/img/flags/es.png", content)
        self.assertIn(">español</button>", content)
        self.assertIn("common/img/flags/en-us.png", content)
