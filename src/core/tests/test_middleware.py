"""
Unit tests for janeway core middleware
"""
from django.contrib.auth.models import AnonymousUser
from django.shortcuts import redirect
from django.test import TestCase, override_settings
from django.test.client import RequestFactory
from django.urls import reverse
from django.core.management import call_command

from core.middleware import (
    SiteSettingsMiddleware,
    TimezoneMiddleware,
    BaseMiddleware
)
from core.models import Account
from journal.tests.utils import make_test_journal
from press.models import Press
from utils.testing import helpers


class TestSiteMiddleware(TestCase):

    def setUp(self):
        journal_kwargs = dict(
            code="test",
            domain="journal.org"
        )
        press_kwargs = dict(
            domain="press.org",
        )
        self.middleware = SiteSettingsMiddleware(BaseMiddleware)
        self.request_factory = RequestFactory()
        self.journal = make_test_journal(**journal_kwargs)
        self.press = Press(**press_kwargs)
        self.press.save()

    @override_settings(URL_CONFIG="path")
    def test_journal_site_in_path_mode(self):
        #expect
        expected_path_info = ("/")
        expected_journal = self.journal
        expected_press = self.press
        expected_site_type = expected_journal

        #do
        request = self.request_factory.get("http://press.org/test/")
        _response = self.middleware.process_request(request)

        #assert
        self.assertEqual(expected_journal, request.journal)
        self.assertEqual(expected_press, request.press)
        self.assertEqual(expected_site_type, request.site_type)

    @override_settings(URL_CONFIG="domain", DEBUG=False)
    def test_journal_site_with_path_in_domain_mode(self):
        # expect
        expected_journal = self.journal
        # do
        request = self.request_factory.get("http://press.org/test/")
        _ = self.middleware.process_request(request)

        # assert
        self.assertEqual(expected_journal, request.journal)

    @override_settings(URL_CONFIG="path")
    def test_press_site_in_path_mode(self):
        #expect
        expected_path_info = ("/")
        expected_journal = None
        expected_press = self.press
        expected_site_type = expected_press

        #do
        request = self.request_factory.get("/", SERVER_NAME="press.org")
        _response = self.middleware.process_request(request)

        #assert
        self.assertEqual(expected_journal, request.journal)
        self.assertEqual(expected_press, request.press)
        self.assertEqual(expected_site_type, request.site_type)

    @override_settings(URL_CONFIG="domain")
    def test_journal_site_in_domain_mode(self):
        #expect
        expected_path_info = ("/")
        expected_journal = self.journal
        expected_press = self.press
        expected_site_type = expected_journal

        #do
        request = self.request_factory.get("/", SERVER_NAME="journal.org")
        _response = self.middleware.process_request(request)

        #assert
        self.assertEqual(expected_journal, request.journal)
        self.assertEqual(expected_press, request.press)
        self.assertEqual(expected_site_type, request.site_type)

    @override_settings(URL_CONFIG="domain")
    def test_press_site_in_domain_mode(self):
        #expect
        expected_path_info = ("/")
        expected_journal = None
        expected_press = self.press
        expected_site_type = expected_press

        #do
        request = self.request_factory.get("/", SERVER_NAME="press.org")
        _response = self.middleware.process_request(request)

        #assert
        self.assertEqual(expected_journal, request.journal)
        self.assertEqual(expected_press, request.press)
        self.assertEqual(expected_site_type, request.site_type)

    @override_settings(URL_CONFIG="path")
    def test_reverse_in_path_mode(self):
        #expect
        expected_index_path = "/test/"

        #do
        request = self.request_factory.get("/test/", SERVER_NAME="press.org")
        _response = self.middleware.process_request(request)
        response = redirect(reverse("website_index"))

        self.assertRedirects(
            response,
            expected_index_path,
            status_code=302,
            fetch_redirect_response=False,
        )


class TestTimezoneMiddleware(TestCase):

    def setUp(self):
        journal_kwargs = dict(
            code="test",
            domain="journal.org"
        )
        press_kwargs = dict(
            domain="press.org",
        )
        self.middleware = TimezoneMiddleware(BaseMiddleware)
        self.request_factory = RequestFactory()
        self.journal = make_test_journal(**journal_kwargs)
        self.press = Press(**press_kwargs)
        self.press.save()

        self.regular_user = helpers.create_user("regularuser@timezone.com")
        self.regular_user.is_active = True
        self.regular_user.save()

    @override_settings(URL_CONFIG="path")
    def test_default_case(self):
        user = AnonymousUser()

        request = self.request_factory.get("/test/", SERVER_NAME="press.org")
        request.session = {}
        request.user = user

        response = self.middleware.process_request(request)

        self.assertEqual(request.timezone, None)

    def test_user_preference_case(self):
        request = self.request_factory.get("/test/", SERVER_NAME="press.org")
        request.session = {}
        user = Account.objects.get(email='regularuser@timezone.com')
        user.preferred_timezone = "Europe/London"
        user.save()

        request.user = user
        response = self.middleware.process_request(request)
        self.assertEqual(request.timezone.zone, user.preferred_timezone)

    def test_browser_timezone_case(self):
        user = AnonymousUser()
        tzname = "Atlantic/Canary"

        request = self.request_factory.get("/test/", SERVER_NAME="press.org")
        request.session = {}
        request.session["janeway_timezone"] = tzname
        request.user = user

        response = self.middleware.process_request(request)

        self.assertEqual(request.timezone.zone, tzname)

    def test_user_preference_over_browser(self):
        user_timezone = "Europe/Madrid"
        browser_timezone = "Atlantic/Canary"

        user = Account.objects.get(email='regularuser@timezone.com')
        user.preferred_timezone = user_timezone
        user.save()

        request = self.request_factory.get("/test/", SERVER_NAME="press.org")
        request.session = {}
        request.session["janeway_timezone"] = browser_timezone
        request.user = user

        response = self.middleware.process_request(request)

        self.assertEqual(request.timezone.zone, user_timezone)


