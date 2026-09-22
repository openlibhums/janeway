from datetime import timedelta

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core import models as core_models
from core.homepage_elements.featured import hooks, models
from submission import models as submission_models
from utils.testing import helpers


class FeaturedArticlesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.editor = helpers.create_editor(cls.journal_one)
        cls.published_article = helpers.create_article(
            cls.journal_one,
            stage=submission_models.STAGE_PUBLISHED,
            date_published=timezone.now() - timedelta(days=1),
        )
        cls.accepted_article = helpers.create_article(
            cls.journal_one,
            stage=submission_models.STAGE_ACCEPTED,
            date_published=timezone.now() - timedelta(days=1),
        )
        cls.scheduled_article = helpers.create_article(
            cls.journal_one,
            stage=submission_models.STAGE_PUBLISHED,
            date_published=timezone.now() + timedelta(days=1),
        )
        cls.homepage_element = core_models.HomepageElement.objects.create(
            name="Featured Articles",
            configure_url="featured_articles_setup",
            template_path="journal/homepage_elements/featured.html",
            content_type=ContentType.objects.get_for_model(cls.journal_one),
            object_id=cls.journal_one.pk,
            has_config=True,
        )
        cls.setup_url = reverse("featured_articles_setup")

    def setUp(self):
        self.client.force_login(self.editor)

    def test_candidate_list_only_contains_published_articles(self):
        response = self.client.get(self.setup_url)
        candidates = list(response.context["articles"])
        self.assertIn(self.published_article, candidates)
        self.assertNotIn(self.accepted_article, candidates)
        self.assertNotIn(self.scheduled_article, candidates)

    def test_published_article_can_be_featured(self):
        response = self.client.post(
            self.setup_url,
            {"article_id": self.published_article.pk},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            models.FeaturedArticle.objects.filter(
                article=self.published_article,
                journal=self.journal_one,
            ).exists()
        )

    def test_unpublished_article_cannot_be_featured(self):
        response = self.client.post(
            self.setup_url,
            {"article_id": self.accepted_article.pk},
        )
        self.assertEqual(response.status_code, 404)
        self.assertFalse(
            models.FeaturedArticle.objects.filter(
                article=self.accepted_article,
            ).exists()
        )

    def test_homepage_hook_excludes_unpublished_articles(self):
        for article in (self.published_article, self.accepted_article):
            models.FeaturedArticle.objects.get_or_create(
                article=article,
                journal=self.journal_one,
                defaults={"added_by": self.editor},
            )
        request = helpers.Request(
            journal=self.journal_one,
            user=self.editor,
        )
        context = hooks.yield_homepage_element_context(
            request,
            core_models.HomepageElement.objects.filter(name="Featured Articles"),
        )
        featured = [fa.article for fa in context["featured_articles"]]
        self.assertIn(self.published_article, featured)
        self.assertNotIn(self.accepted_article, featured)
