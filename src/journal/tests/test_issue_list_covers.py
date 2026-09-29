__copyright__ = "Copyright 2026 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from bs4 import BeautifulSoup
from django.test import TestCase, override_settings
from django.urls import reverse

from utils.shared import clear_cache
from utils.testing import helpers


@override_settings(URL_CONFIG="domain")
class ClarityIssueListCoverTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal, _ = helpers.create_journals()
        cls.journal.default_cover_image.name = "cover_images/journal-cover.png"
        cls.journal.save()
        cls.with_cover = helpers.create_issue(cls.journal, vol=1, number=1)
        cls.with_cover.cover_image.name = "cover_images/issue-cover.png"
        cls.with_cover.save()
        cls.without_cover = helpers.create_issue(cls.journal, vol=1, number=2)

    def setUp(self):
        clear_cache()

    def cover_sources(self):
        response = self.client.get(
            reverse("journal_issues"),
            {"theme": "clarity"},
            SERVER_NAME=self.journal.domain,
        )
        soup = BeautifulSoup(response.content.decode(), "html.parser")
        return [img["src"] for img in soup.select(".issue-cover img")]

    def test_issues_without_a_cover_use_the_journal_default_cover(self):
        sources = self.cover_sources()
        self.assertIn(self.with_cover.cover_image.url, sources)
        self.assertIn(self.journal.default_cover_image.url, sources)
        self.assertEqual(len(sources), 2)

    def test_no_cover_is_shown_without_a_journal_default(self):
        self.journal.default_cover_image = None
        self.journal.save()
        self.assertEqual(self.cover_sources(), [self.with_cover.cover_image.url])
