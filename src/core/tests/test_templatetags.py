from datetime import datetime, timedelta

import pytz
from django.utils import timezone
from django.test import TestCase, override_settings
from freezegun import freeze_time

from utils.testing import helpers
from core.templatetags import fqdn, dates
from django.test import TestCase, override_settings, RequestFactory
from core.templatetags import fqdn, dates
from django.utils.translation import activate
from django.conf import settings
from django.template.exceptions import TemplateSyntaxError


class TestFqdn(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.journal_two.domain = None
        cls.journal_two.save()

    def test_stateless_site_url_for_press(self):
        url_name = "press_all_users"
        url = fqdn.stateless_site_url(self.press, url_name)
        self.assertEqual(url, "http://localhost/press/user/all/")

    @override_settings(URL_CONFIG="domain")
    def test_stateless_site_url_for_journal_domain(self):
        url_name = "journal_users"
        url = fqdn.stateless_site_url(self.journal_one, url_name)
        self.assertEqual(url, f"http://{self.journal_one.domain}/user/all/")

    @override_settings(URL_CONFIG="path")
    def test_stateless_site_url_for_journal_path(self):
        url_name = "journal_users"
        url = fqdn.stateless_site_url(self.journal_two, url_name)
        self.assertEqual(
            url,
            f"http://{self.journal_two.press.domain}/{self.journal_two.code}/user/all/",
        )


ny_tz = pytz.timezone("America/New_York")
frozen_dt = timezone.make_aware(
    datetime(2025, 3, 26, 12, 0, 0),
    timezone=ny_tz,
)


@freeze_time(frozen_dt)
class TestOffsetDateTag(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_default = helpers.create_user("default@example.com")
        cls.user_tz = helpers.create_user(
            "tz@example.com",
            preferred_timezone="Europe/London",
        )
        cls.user_bad_tz = helpers.create_user(
            "bad@example.com",
            preferred_timezone="MemoryAlpha/Library",
        )

        cls.request_default = type("Request", (), {"user": cls.user_default})()
        cls.request_tz = type("Request", (), {"user": cls.user_tz})()
        cls.request_bad_tz = type("Request", (), {"user": cls.user_bad_tz})()

    def test_offset_date_with_default_timezone_datetime(self):
        """
        Test offset_date tag with default timezone and datetime-local input.
        """
        context = {"request": self.request_default}
        result = dates.offset_date(
            context,
            days=2,
            input_type="datetime-local",
        )
        expected = (timezone.now() + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M")
        self.assertEqual(result, expected)

    def test_offset_date_with_preferred_timezone_datetime(self):
        """
        Test offset_date tag with a valid preferred timezone and datetime-local input.
        """
        context = {"request": self.request_tz}
        london = pytz.timezone("Europe/London")
        expected_due = timezone.now().astimezone(london) + timedelta(days=1)
        expected = expected_due.strftime("%Y-%m-%dT%H:%M")

        result = dates.offset_date(
            context,
            days=1,
            input_type="datetime-local",
        )
        self.assertEqual(result, expected)

    def test_offset_date_with_invalid_timezone_datetime(self):
        """
        Test offset_date tag with an invalid preferred timezone and datetime-local input.
        Should fall back to default timezone.
        """
        context = {"request": self.request_bad_tz}
        expected = (timezone.now() + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M")

        result = dates.offset_date(
            context,
            days=1,
            input_type="datetime-local",
        )
        self.assertEqual(result, expected)

    def test_offset_date_with_default_timezone_date(self):
        """
        Test offset_date tag with default timezone and date input.
        """
        context = {"request": self.request_default}
        expected = (timezone.now() + timedelta(days=2)).strftime("%Y-%m-%d")

        result = dates.offset_date(
            context,
            days=2,
            input_type="date",
        )
        self.assertEqual(result, expected)


class TestDateHuman(TestCase):
    # Define the languages we want to test
    test_languages = {
        "en": "English",
        "en-us": "English (US)",
        "fr": "French",
        "de": "German",
        "nl": "Dutch",
        "cy": "Welsh",
        "es": "Spanish",
    }

    @classmethod
    def setUpTestData(cls):
        """sets up all the data for testing"""
        cls.test_dates = {
            "date": datetime(2023, 12, 3),  # 3 December 2023
            "leap_year": datetime(2024, 2, 29),  # 29 February 2024
            "new_year": datetime(2021, 1, 1),  # 1 January 2021
        }
        cls.expected_formats = {
            "date": {
                "en": "3 December 2023",
                "en-us": "3 December 2023",
                "fr": "3 décembre 2023",
                "de": "3 Dezember 2023",
                "nl": "3 december 2023",
                "cy": "3 Rhagfyr 2023",
                "es": "3 diciembre 2023",
            },
            "leap_year": {
                "en": "29 February 2024",
                "en-us": "29 February 2024",
                "fr": "29 février 2024",
                "de": "29 Februar 2024",
                "nl": "29 februari 2024",
                "cy": "29 Chwefror 2024",
                "es": "29 febrero 2024",
            },
            "new_year": {
                "en": "1 January 2021",
                "en-us": "1 January 2021",
                "fr": "1 janvier 2021",
                "de": "1 Januar 2021",
                "nl": "1 januari 2021",
                "cy": "1 Ionawr 2021",
                "es": "1 enero 2021",
            },
        }
        cls.test_non_dates = {
            "empty_string": "",
            "string": "2023,12,3",
            "int": 134567,
            "zero": 0,
            "none": None,
        }

    def test_non_dates_debug_true(self):
        """Test date_human hides input errors except when settings.DEBUG=True."""
        with override_settings(DEBUG=True):
            for key, test_non_date in self.test_non_dates.items():
                with self.subTest(non_date=key):
                    with self.assertRaises(TemplateSyntaxError) as context:
                        dates.date_human(test_non_date)
                    self.assertEqual(
                        str(context.exception),
                        "The value filtered by `date_human` must be a `datetime.datetime`",
                        f"Failed for non-existent date '{key}' . Expected TemplateSyntaxError.",
                    )

    def test_non_dates_debug_false(self):
        """Test date_human hides input errors except when settings.DEBUG=False."""
        with override_settings(DEBUG=False):
            for key, test_non_date in self.test_non_dates.items():
                with self.subTest(non_date=key):
                    result = dates.date_human(test_non_date)
                    self.assertEqual(
                        result,
                        "",
                        f"Failed for {key}.  Expected hidden error (i.e. empty string), actual '{result}'.",
                    )

    @override_settings(LANGUAGES=test_languages)
    def test_date_human_all_languages(self):
        """Test date_human with all supported languages that have complete test data"""
        for key, test_date in self.test_dates.items():
            for lang_code, expected in self.expected_formats[key].items():
                with self.subTest(date=key, code=lang_code):
                    activate(lang_code)
                    result = dates.date_human(test_date)
                    expected = self.expected_formats[key].get(lang_code)
                    self.assertEqual(
                        result,
                        expected,
                        f"Failed for {lang_code}.  Expected '{expected}', actual '{result}'.",
                    )

    @override_settings(LANGUAGES=test_languages)
    def test_date_human_browser_languages(self):
        """Test data_human uses application language regardless of browser language setting"""
        supported_languages = list(self.test_languages.keys())

        non_supported_languages = ["ja", "en-nz", "es-ni", "ar-sa"]

        browser_languages = supported_languages + non_supported_languages

        factory = RequestFactory()

        def set_browser_lang(lang_code):
            request = factory.get("/")
            request.META["HTTP_ACCEPT_LANGUAGE"] = lang_code

        for lang in browser_languages:
            set_browser_lang(lang)
            self.test_date_human_all_languages()
