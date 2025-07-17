from django.test import TestCase, override_settings
from django.test.client import RequestFactory
from django.urls import reverse
from django.urls.base import clear_script_prefix

from core.middleware import SiteSettingsMiddleware
from journal import models
from journal.tests.utils import make_test_journal
from press.models import Press
from utils.testing import helpers


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

    def tearDown(self):
        clear_script_prefix()

    @override_settings(URL_CONFIG="path")
    def test_path_mode_site_url_for_journal_in_context(self):
        request = self.request_factory.get(
            "/test/banana/", SERVER_NAME="sitetestpress.org"
        )
        request.journal = self.journal
        request.press = self.press

        with helpers.request_context(request):
            result = self.journal.site_url()

        expected = "http://sitetestpress.org/modeltests"

        self.assertEqual(expected, result)

    @override_settings(URL_CONFIG="path")
    def test_path_mode_site_url_for_journal_in_context_with_path(self):
        response = self.client.get(
            "/modeltests/banana", SERVER_NAME="sitetestpress.org"
        )
        path = reverse("website_index")
        result = self.journal.site_url(path)

        expected = "http://" + self.press.domain + path

        self.assertEqual(expected, result)

    @override_settings(URL_CONFIG="path")
    def test_path_mode_site_url_for_other_site(self):
        other_journal = make_test_journal(
            code="ojwithpath",
            domain="ojwithpath.org",
        )
        response = self.client.get("/ojwithpath/banana", SERVER_NAME="sitetest.org")
        result = self.journal.site_url()

        expected = "http://{}/{}".format(
            self.press.domain,
            self.journal.code,
        )

        self.assertEqual(expected, result)

    @override_settings(URL_CONFIG="domain")
    def test_domain_mode_site_url_for_journal_in_context(self):
        response = self.client.get("/modeltests/banana", SERVER_NAME="sitetest.org")
        result = self.journal.site_url()

        expected = "http://" + self.journal.domain

        self.assertEqual(expected, result)

    @override_settings(URL_CONFIG="domain")
    def test_domain_mode_site_url_for_other_site(self):
        other_journal = make_test_journal(
            code="ojwithdomain",
            domain="ojwithdomain.org",
        )
        response = self.client.get("/banana", SERVER_NAME="ojwithdomain.org")
        result = self.journal.site_url()

        expected = "http://" + self.journal.domain

        self.assertEqual(expected, result)


class TestIssueModel(TestCase):
    def setUp(self):
        self.press = helpers.create_press()
        self.journal, _ = helpers.create_journals()
        self.issue = helpers.create_issue(self.journal, 1, 1)       
        self.expected_results = {
            'issue_1': {
                'display_title': (
                    "Volume 1 &bull; Issue 1 &bull; 2022 &bull;"
                    " Test Issue from Utils Testing Helpers"
                ),
                'display_title_a11y': (
                    "Volume 1, Issue 1, 2022,"
                    " Test Issue from Utils Testing Helpers"
                )
            },
            'issue_2': {
                'display_title': (
                    "Volume 1 &bull; Issue 2 &bull; 2022 &bull;"
                    " Test Issue from Utils Testing Helpers"
                ),
                'display_title_a11y': (
                    "Volume 1, Issue 2, 2022,"
                    " Test Issue from Utils Testing Helpers"
                )
            },
            'issue_1_no_number': {
                'display_title': (
                    "Volume 1 &bull; 2022 &bull;"
                    " Test Issue from Utils Testing Helpers"
                ),
                'display_title_a11y': (
                    "Volume 1, 2022,"
                    " Test Issue from Utils Testing Helpers"
                )
            },
            'collection': {
                'display_title': "Test Issue from Utils Testing Helpers",
                'display_title_a11y': "Test Issue from Utils Testing Helpers"
            }
        }

    def test_issue_display_title(self):
        self.assertEqual(self.issue.display_title, self.expected_results['issue_1']['display_title'])
        self.assertEqual(self.issue.display_title_a11y, self.expected_results['issue_1']['display_title_a11y'])

    def test_collection_display_title(self):
        self.issue.issue_type = models.IssueType.objects.get(
            code="collection",
            journal=self.journal,
        )
        self.issue.save()
        # Reload issue
        issue = models.Issue.objects.get(id=self.issue.id)
        self.assertEqual(issue.display_title, self.expected_results['collection']['display_title'])
        self.assertEqual(issue.display_title_a11y, self.expected_results['collection']['display_title_a11y'])

    def test_issue_display_title_changed(self):
        self.issue.issue = 2
        self.issue.save()
        self.assertEqual(self.issue.display_title, self.expected_results['issue_2']['display_title'])
        self.assertEqual(self.issue.display_title_a11y, self.expected_results['issue_2']['display_title_a11y'])

    def test_journal_settings_for_display_title_changed(self):
        self.journal.display_issue_number = False
        self.journal.save()
        # Reload issue
        issue = models.Issue.objects.get(id=self.issue.id)
        self.assertEqual(issue.display_title, self.expected_results['issue_1_no_number']['display_title'])
        self.assertEqual(issue.display_title_a11y, self.expected_results['issue_1_no_number']['display_title_a11y'])