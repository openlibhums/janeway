__copyright__ = "Copyright 2026 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

import re

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from utils.shared import clear_cache
from utils.testing import helpers


@override_settings(URL_CONFIG="domain")
class MaterialArticleSidebarHeadingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.article = helpers.create_article(
            journal=cls.journal_one,
            with_author=True,
            stage="Published",
            date_published=timezone.now() - timezone.timedelta(days=1),
        )

    def setUp(self):
        clear_cache()

    def test_author_and_downloads_headings_are_level_two(self):
        response = self.client.get(
            reverse(
                "article_view",
                kwargs={"identifier_type": "id", "identifier": self.article.pk},
            ),
            {"theme": "material"},
            SERVER_NAME=self.journal_one.domain,
        )
        content = response.content.decode()
        self.assertRegex(content, r"<h2>\s*Author\s*</h2>")
        self.assertRegex(content, r"<h2>\s*Downloads\s*</h2>")
        self.assertIsNone(re.search(r"<h4>", content))
