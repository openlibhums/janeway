from datetime import timedelta

import pytz
from django.utils import timezone
from django.test import TestCase, override_settings
from freezegun import freeze_time

from utils.testing import helpers
from core.templatetags import fqdn, dates

class TestFqdn(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.journal_two.domain = None
        cls.journal_two.save()

    def test_stateless_site_url_for_press(self):
        url_name = 'press_all_users' 
        url = fqdn.stateless_site_url(self.press, url_name)
        self.assertEqual(url, 'http://localhost/press/user/all/')

    @override_settings(URL_CONFIG="domain")
    def test_stateless_site_url_for_journal_domain(self):
        url_name = 'journal_users' 
        url = fqdn.stateless_site_url(self.journal_one, url_name)
        self.assertEqual(url, f'http://{self.journal_one.domain}/user/all/')

    @override_settings(URL_CONFIG="path")
    def test_stateless_site_url_for_journal_path(self):
        url_name = 'journal_users' 
        url = fqdn.stateless_site_url(self.journal_two, url_name)
        self.assertEqual(url, f'http://{self.journal_two.press.domain}/{self.journal_two.code}/user/all/')


@freeze_time("2025-03-26 12:00:00")
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
        expected = "2025-03-28T12:00"
        self.assertEqual(result, expected)

    def test_offset_date_with_preferred_timezone_datetime(self):
        """
        Test offset_date tag with a valid preferred timezone and datetime-local input.
        """
        context = {"request": self.request_tz}
        # 12:00 UTC is 12:00 GMT in March (not in daylight saving yet)
        result = dates.offset_date(
            context,
            days=1,
            input_type="datetime-local",
        )
        expected = "2025-03-27T12:00"
        self.assertEqual(result, expected)

    def test_offset_date_with_invalid_timezone_datetime(self):
        """
        Test offset_date tag with an invalid preferred timezone and datetime-local input.
        Should fall back to default timezone.
        """
        context = {"request": self.request_bad_tz}
        result = dates.offset_date(
            context,
            days=1,
            input_type="datetime-local",
        )
        expected = "2025-03-27T12:00"
        self.assertEqual(result, expected)

    def test_offset_date_with_default_timezone_date(self):
        """
        Test offset_date tag with default timezone and date input.
        """
        context = {"request": self.request_default}
        result = dates.offset_date(
            context,
            days=2,
            input_type="date",
        )
        expected = "2025-03-28"
        self.assertEqual(result, expected)