__copyright__ = "Copyright 2026 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from django.test import TestCase, override_settings
from django.urls import reverse

from utils.shared import clear_cache
from utils.testing import helpers


@override_settings(URL_CONFIG="domain")
class IssueLinkLabelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.issue_one = helpers.create_issue(cls.journal_one, vol=1, number=1)
        cls.issue_two = helpers.create_issue(cls.journal_one, vol=1, number=2)
        cls.journal_one.current_issue = cls.issue_two
        cls.journal_one.save()

    def setUp(self):
        clear_cache()

    def test_clean_current_issue_link_is_labelled_with_current_issue(self):
        response = self.client.get(
            reverse("journal_issues"),
            {"theme": "clean"},
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertContains(
            response,
            f"aria-label='{self.issue_two.display_title_a11y} (0 items)'",
        )
        self.assertNotContains(response, "aria-label=' (")


@override_settings(URL_CONFIG="domain")
class JournalLogoFallbackTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()

    def setUp(self):
        clear_cache()

    def test_fallback_logo_has_alt_text(self):
        for theme in ["OLH", "material"]:
            with self.subTest(theme=theme):
                response = self.client.get(
                    reverse("website_index"),
                    {"theme": theme},
                    SERVER_NAME=self.journal_one.domain,
                )
                self.assertContains(
                    response,
                    f'sample/janeway.png" alt="{self.journal_one.name}"',
                )
