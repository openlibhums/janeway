from unittest.mock import patch, Mock

from django.shortcuts import reverse
from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time

from submission import models as submission_models
from rss import views as rss_views
from utils.testing import helpers

FROZEN_DATETIME_2012 = timezone.make_aware(timezone.datetime(2012, 1, 14, 0, 0, 0))


class TestRSS(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.hidden_journal = helpers.create_journals()
        cls.hidden_journal.hide_from_press = True
        cls.hidden_journal.save()
        cls.published_article = helpers.create_article(
            cls.journal_one,
            with_author=True,
            stage=submission_models.STAGE_PUBLISHED,
            date_published=FROZEN_DATETIME_2012,
            title="Published article",
        )
        cls.hidden_article = helpers.create_article(
            cls.hidden_journal,
            with_author=True,
            stage=submission_models.STAGE_PUBLISHED,
            date_published=FROZEN_DATETIME_2012,
            title="Article published in hidden journal",
        )

    def test_journal_articles_feed(self):
        feed = rss_views.LatestArticlesFeed()
        expected = set([self.published_article])
        result = set(item for item in feed.items(self.journal_one))
        self.assertSetEqual(expected, result)

    def test_press_articles_feed(self):
        feed = rss_views.LatestArticlesFeed()
        expected = set([self.published_article])
        result = set(item for item in feed.items(self.press))
        self.assertSetEqual(expected, result)
