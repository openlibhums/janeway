from django.core.cache import cache
from django.test import TestCase

from core.homepage_elements.popular import logic
from metrics import models as metrics_models
from submission import models as submission_models
from utils.testing import helpers


class TestMostPopularArticles(TestCase):
    @classmethod
    def setUpTestData(cls):
        helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.quiet_article = helpers.create_article(
            cls.journal_one,
            title="Quiet article",
            stage=submission_models.STAGE_PUBLISHED,
        )
        cls.busy_article = helpers.create_article(
            cls.journal_one,
            title="Busy article",
            stage=submission_models.STAGE_PUBLISHED,
        )
        for article, count in [(cls.quiet_article, 1), (cls.busy_article, 3)]:
            for i in range(count):
                metrics_models.ArticleAccess.objects.create(
                    article=article,
                    type="view",
                    identifier="reader-{}".format(i),
                )

    def setUp(self):
        cache.clear()

    def test_articles_ordered_by_access_count(self):
        articles = logic.get_most_popular_articles(self.journal_one, 2, "weekly")

        self.assertEqual(articles, [self.busy_article, self.quiet_article])

    def test_articles_limited_to_number(self):
        articles = logic.get_most_popular_articles(self.journal_one, 1, "weekly")

        self.assertEqual(articles, [self.busy_article])
