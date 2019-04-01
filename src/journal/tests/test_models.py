from django.test import TestCase, override_settings
from django.test.client import RequestFactory
from django.urls import reverse

from core.middleware import SiteSettingsMiddleware
from journal.tests.utils import make_test_journal
from press.models import Press
from utils.testing.helpers import request_context

class TestJournalSite(TestCase):

    def setUp(self):
        self.request_factory = RequestFactory()
        self.press = Press(domain="sitetestpress.org")
        self.press.save()
        self.request_factory
        journal_kwargs = dict(
            code="modeltests",
            domain="sitetest.org",
        )
        self.journal = make_test_journal(**journal_kwargs)

    @override_settings(URL_CONFIG="path")
    def test_path_mode_site_url_for_journal_in_context(self):
        request = self.request_factory.get(
                "/test/banana/", SERVER_NAME="sitetestpress.org")
        request.journal = self.journal
        request.press = self.press

        with request_context(request):
            result = self.journal.site_url()

        expected = "http://sitetestpress.org/modeltests"

        self.assertEqual(expected, result)

    @override_settings(URL_CONFIG="path")
    def test_path_mode_site_url_for_journal_in_context_with_path(self):
        response = self.client.get(
                "/modeltests/banana", SERVER_NAME="sitetestpress.org")
        path = reverse("website_index")
        result = self.journal.site_url(path)

        expected = "http://" + self.press.domain + path

        self.assertEqual(expected, result)

    @override_settings(URL_CONFIG="path")
    def test_path_mode_site_url_for_other_site(self):
        other_journal = make_test_journal(
            code="otherjournalwithpath",
            domain="otherjournalwithpath.org",
        )
        response = self.client.get(
            "/otherjournalwithpath/banana", SERVER_NAME="sitetest.org")
        result = self.journal.site_url()

        expected = "http://{}/{}".format(
                self.press.domain,
                self.journal.code,
        )

        self.assertEqual(expected, result)

    @override_settings(URL_CONFIG="domain")
    def test_domain_mode_site_url_for_journal_in_context(self):
        response = self.client.get(
                "/modeltests/banana", SERVER_NAME="sitetest.org")
        result = self.journal.site_url()

        expected = "http://" + self.journal.domain

        self.assertEqual(expected, result)

    @override_settings(URL_CONFIG="domain")
    def test_domain_mode_site_url_for_journal_in_context_with_path(self):
        response = self.client.get(
                "/modeltests/banana", SERVER_NAME="sitetestpress.org")
        path = reverse("website_index")
        result = self.journal.site_url(path)

        expected = "http://" + self.journal.domain + path

        self.assertEqual(expected, result)

    @override_settings(URL_CONFIG="domain")
    def test_domain_mode_site_url_for_other_site(self):
        other_journal = make_test_journal(
            code="otherjournalwithdomain",
            domain="otherjournalwithdomain.org",
        )
        response = self.client.get(
            "/banana", SERVER_NAME="otherjournalwithdomain.org")
        result = self.journal.site_url()

        expected = "http://" + self.journal.domain

        self.assertEqual(expected, result)
