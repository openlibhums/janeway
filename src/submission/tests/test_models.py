__copyright__ = "Copyright 2025 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from urllib.parse import urlparse

from django.core.cache import cache
from django.db import IntegrityError
from django.test import TestCase, override_settings
from django.urls.base import clear_script_prefix

from submission import models
from utils.testing import helpers


class FrozenAuthorModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.article_one = helpers.create_article(cls.journal_one)
        cls.frozen_author = models.FrozenAuthor.objects.create(
            article=cls.article_one,
            name_prefix="Dr.",
            first_name="S.",
            middle_name="Bella",
            last_name="Rogers",
            name_suffix="Esq.",
        )

    def test_full_name(self):
        self.assertEqual("Dr. S. Bella Rogers Esq.", self.frozen_author.full_name())

    def test_credits(self):
        self.frozen_author.add_credit("conceptualization")
        self.assertEqual(
            self.frozen_author.credits.first().get_role_display(),
            "Conceptualization",
        )


class CreditRecordTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.article_one = helpers.create_article(cls.journal_one)
        cls.frozen_author_one = helpers.create_frozen_author(cls.article_one)

    def test_article_authors_and_credits_for_frozen_author(self):
        role = self.frozen_author_one.add_credit("writing-original-draft")
        expected_frozen_authors = [
            fa for fa, _ in self.article_one.authors_and_credits().items()
        ]
        self.assertEqual(expected_frozen_authors, [self.frozen_author_one])
        expected_roles = [
            roles for _, roles in self.article_one.authors_and_credits().items()
        ]
        self.assertEqual(expected_roles[0].first(), role)


class ArticleURLTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.article_one = helpers.create_article(cls.journal_one)

    def setUp(self):
        cache.clear()
        clear_script_prefix()

    def tearDown(self):
        clear_script_prefix()
        cache.clear()
        helpers.clear_current_request()

    @override_settings(URL_CONFIG="domain", DEBUG=False)
    def test_article_url_generated_in_path_mode_is_not_reused_in_domain_mode(self):
        path_mode_request = helpers.browse(
            f"http://{self.press.domain}/{self.journal_one.code}/articles/",
        )
        self.assertEqual(path_mode_request.site_object, self.journal_one)
        path_mode_url = self.article_one.url
        self.assertIn(self.journal_one.code, path_mode_url.split("//")[-1])

        domain_mode_request = helpers.browse(
            f"http://{self.journal_one.domain}/articles/",
        )
        self.assertEqual(domain_mode_request.site_object, self.journal_one)
        expected_url = (
            f"http://{self.journal_one.domain}/article/id/{self.article_one.pk}/"
        )
        self.assertEqual(self.article_one.url, expected_url)

    @override_settings(URL_CONFIG="domain", DEBUG=False)
    def test_article_url_cached_separately_per_entry_point(self):
        expected_domain_url = (
            f"http://{self.journal_one.domain}/article/id/{self.article_one.pk}/"
        )
        path_prefix = f"/{self.journal_one.code}"

        helpers.browse(f"http://{self.journal_one.domain}/articles/")
        self.assertEqual(self.article_one.url, expected_domain_url)

        helpers.browse(f"http://{self.press.domain}{path_prefix}/articles/")
        path_mode_url = self.article_one.url
        self.assertNotEqual(path_mode_url, expected_domain_url)
        self.assertTrue(urlparse(path_mode_url).path.startswith(path_prefix))

        helpers.browse(f"http://{self.journal_one.domain}/articles/")
        self.assertEqual(self.article_one.url, expected_domain_url)

    @override_settings(URL_CONFIG="domain", DEBUG=False)
    def test_article_url_without_request_unaffected_by_path_mode_render(self):
        helpers.browse(f"http://{self.press.domain}/{self.journal_one.code}/articles/")
        path_mode_url = self.article_one.url
        self.assertIn(f"/{self.journal_one.code}", urlparse(path_mode_url).path)

        helpers.clear_current_request()
        clear_script_prefix()
        expected_domain_url = (
            f"http://{self.journal_one.domain}/article/id/{self.article_one.pk}/"
        )
        self.assertEqual(self.article_one.url, expected_domain_url)
