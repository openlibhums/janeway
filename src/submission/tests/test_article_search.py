__copyright__ = "Copyright 2025 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

import os

from django.core.management import call_command
from django.test import TransactionTestCase
from django.conf import settings
from django.test.utils import override_settings
from django.utils import timezone

import swapper

from core.models import File
from journal import models as journal_models
from submission import models
from utils.install import update_xsl_files, update_settings, update_issue_types
from utils.testing import helpers
from utils.testing.helpers import create_galley

FROZEN_DATETIME_2020 = timezone.make_aware(timezone.datetime(2020, 1, 1, 0, 0, 0))
FROZEN_DATETIME_1990 = timezone.make_aware(timezone.datetime(1990, 1, 1, 12, 0, 0))


class ArticleSearchTests(TransactionTestCase):
    roles_path = os.path.join(settings.BASE_DIR, "utils", "install", "roles.json")
    fixtures = [roles_path]

    @staticmethod
    def create_journal():
        """
        Creates a dummy journal for testing
        :return: a journal
        """
        update_xsl_files()
        update_settings()
        journal_one = journal_models.Journal(code="TST", domain="testserver")
        journal_one.title = "Test Journal: A journal of tests"
        journal_one.save()
        update_issue_types(journal_one)

        return journal_one

    def create_authors(self):
        author_1_data = {
            "email": "one@example.org",
            "is_active": True,
            "password": "this_is_a_password",
            "salutation": "Prof.",
            "first_name": "Martin",
            "middle_name": "",
            "last_name": "Eve",
            "department": "English & Humanities",
            "institution": "Birkbeck, University of London",
        }
        author_2_data = {
            "email": "two@example.org",
            "is_active": True,
            "password": "this_is_a_password",
            "salutation": "Sr.",
            "first_name": "Mauro",
            "middle_name": "",
            "last_name": "Sanchez",
            "department": "English & Humanities",
            "institution": "Birkbeck, University of London",
        }
        author_1 = helpers.create_author(self.journal_one, **author_1_data)
        author_2 = helpers.create_author(self.journal_one, **author_2_data)

        return author_1, author_2

    def setUp(self):
        """
        Setup the test environment.
        :return: None
        """
        self.journal_one = self.create_journal()
        self.editor = helpers.create_editor(self.journal_one)
        self.press = helpers.create_press()

    @override_settings(ENABLE_FULL_TEXT_SEARCH=True)
    def test_article_full_text_search(self):
        text_to_search = """
            Exceeding reaction chamber thermal limit.
            We have begun power-supply calibration.
            Force fields have been established on all turbo lifts and crawlways.
            Computer, run a level-two diagnostic on warp-drive systems.
        """
        from django.db import connection

        if connection.vendor == "sqlite":
            # No native support for full text search in sqlite
            return
        needle = "turbo lifts"

        article = models.Article.objects.create(
            journal=self.journal_one,
            title="Testing the search of articles",
            date_published=FROZEN_DATETIME_2020,
            stage=models.STAGE_PUBLISHED,
        )
        _other_article = models.Article.objects.create(
            journal=self.journal_one,
            title="This article should not appear",
            date_published=FROZEN_DATETIME_2020,
        )
        file_obj = File.objects.create(article_id=article.pk)
        create_galley(article, file_obj)
        FileText = swapper.load_model("core", "FileText")
        text_to_search = FileText.preprocess_contents(text_to_search)
        text = FileText.objects.create(
            contents=text_to_search,
        )
        file_obj.text = text
        file_obj.save()

        # Mysql can't search at all without FULLTEXT indexes installed
        call_command("generate_search_indexes")

        search_filters = {"full_text": True}
        queryset = models.Article.objects.search(needle, search_filters)
        result = [a for a in queryset]

        self.assertEqual(result, [article])

    @override_settings(ENABLE_FULL_TEXT_SEARCH=True)
    def test_article_search_abstract(self):
        text_to_search = """
            Exceeding reaction chamber thermal limit.
            We have begun power-supply calibration.
            Force fields have been established on all turbo lifts and crawlways.
            Computer, run a level-two diagnostic on warp-drive systems.
        """
        needle = "Crawlways"

        article = models.Article.objects.create(
            journal=self.journal_one,
            title="Test searching abstract",
            date_published=FROZEN_DATETIME_2020,
            stage=models.STAGE_PUBLISHED,
            abstract=text_to_search,
        )
        other_article = models.Article.objects.create(
            journal=self.journal_one,
            title="This article should not appear",
            date_published=FROZEN_DATETIME_2020,
            abstract="Random abstract crawl text",
        )

        # Mysql can't search at all without FULLTEXT indexes installed
        call_command("generate_search_indexes")

        search_filters = {"abstract": True}
        queryset = models.Article.objects.search(needle, search_filters)
        result = [a for a in queryset]

        self.assertEqual(result, [article])

    @override_settings(ENABLE_FULL_TEXT_SEARCH=True)
    def test_article_search_title(self):
        text_to_search = "Computer, run a level-two diagnostic on warp-drive systems."
        needle = "diagnostic"

        article = models.Article.objects.create(
            journal=self.journal_one,
            title=text_to_search,
            date_published=FROZEN_DATETIME_2020,
            stage=models.STAGE_PUBLISHED,
        )
        other_article = models.Article.objects.create(
            journal=self.journal_one,
            title="This article should not appear",
            date_published=FROZEN_DATETIME_2020,
        )

        # Mysql can't search at all without FULLTEXT indexes installed
        call_command("generate_search_indexes")

        search_filters = {"title": True}
        queryset = models.Article.objects.search(needle, search_filters)
        result = [a for a in queryset]

        self.assertEqual(result, [article])
