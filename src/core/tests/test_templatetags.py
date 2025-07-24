from datetime import datetime, timedelta

import pytz
from django.utils import timezone
from django.test import TestCase, override_settings
from django.urls import set_script_prefix
from freezegun import freeze_time

from utils.testing import helpers
from core.templatetags import fqdn, dates


class TestFqdn(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.domain_journal, cls.path_journal = helpers.create_journals()
        cls.path_journal.domain = None
        cls.path_journal.save()

    def test_stateless_site_url_for_press(self):
        url_name = "press_all_users"
        url = fqdn.stateless_site_url(self.press, url_name)
        self.assertEqual(url, "http://localhost/press/user/all/")

    @override_settings(URL_CONFIG="domain")
    def test_stateless_site_url_for_journal_domain(self):
        url_name = "journal_users"
        url = fqdn.stateless_site_url(self.domain_journal, url_name)
        self.assertEqual(url, f"http://{self.domain_journal.domain}/user/all/")

    @override_settings(URL_CONFIG="path")
    def test_stateless_site_url_for_journal_path(self):
        url_name = "journal_users"
        url = fqdn.stateless_site_url(self.path_journal, url_name)
        self.assertEqual(
            url,
            f"http://{self.path_journal.press.domain}/{self.path_journal.code}/user/all/",
        )

    @override_settings(URL_CONFIG="path")
    def test_stateless_site_url_across_journals(self):
        url_name = "journal_users"
        fake_code = "fake_code"
        set_script_prefix(f"/{fake_code}")
        url = fqdn.stateless_site_url(self.path_journal, url_name)
        self.assertFalse(fake_code in url)
        self.assertEqual(
            url,
            f"http://{self.path_journal.press.domain}/{self.path_journal.code}/user/all/",
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
