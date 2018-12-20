"""
Unit tests for janeway core middleware
"""
from django.shortcuts import redirect
from django.test import TestCase, override_settings
from django.test.client import RequestFactory
from django.urls import reverse

from core.middleware import SiteSettingsMiddleware, get_site_resources
from journal.tests.utils import make_test_journal
from journal.models import Journal
from press.models import Press

class TestSiteMiddleware(TestCase):
    def setUp(self):
        journal_kwargs = dict(
            code="test",
            domain="journal.org"
        )
        press_kwargs = dict(
            domain="press.org",
        )
        self.middleware = SiteSettingsMiddleware()
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

