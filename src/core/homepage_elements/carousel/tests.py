__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
from dateutil.relativedelta import relativedelta

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.utils import timezone

from core.homepage_elements.carousel import models
from comms import models as comms_models
from journal import models as journal_models
from submission import models as sm_models
from utils.testing.helpers import create_journals, create_press

FROZEN_DATETIME_20180628 = timezone.make_aware(
    timezone.datetime(2018, 6, 28, 8, 15, 27, 243860)
)
FROZEN_DATETIME_20180629 = timezone.make_aware(
    timezone.datetime(2018, 6, 29, 8, 15, 27, 243860)
)


# Create your tests here.
class TestCarousel(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = create_press()
        cls.journal_one, cls.hidden_journal = create_journals()
        cls.hidden_journal.hide_from_press = True
        cls.hidden_journal.save()
        cls.issue = journal_models.Issue.objects.create(journal=cls.journal_one)
        cls.news_item = comms_models.NewsItem.objects.create(
            posted=FROZEN_DATETIME_20180628,
        )
        cls.news_item.content_type = ContentType.objects.get_for_model(cls.journal_one)
        cls.news_item.object_id = cls.journal_one.id
        cls.article_one = sm_models.Article.objects.create(
            journal=cls.journal_one,
            stage=sm_models.STAGE_PUBLISHED,
            date_published=FROZEN_DATETIME_20180628,
            title="Carousel Article One",
        )
        cls.article_two = sm_models.Article.objects.create(
            journal=cls.journal_one,
            stage=sm_models.STAGE_PUBLISHED,
            date_published=FROZEN_DATETIME_20180629,
            title="Carousel Article Two",
        )
        cls.hidden_article = sm_models.Article.objects.create(
            journal=cls.hidden_journal,
            stage=sm_models.STAGE_PUBLISHED,
            date_published=FROZEN_DATETIME_20180629,
            title="Hidden article",
        )

    def test_carousel(self):
        carousel = models.Carousel.objects.create()
        self.assertFalse(carousel.get_items())

    def test_latest_articles(self):
        carousel = models.Carousel.objects.create(latest_articles=True)
        self.journal_one.carousel = carousel
        self.journal_one.save()
        expected = self.article_two
        result = self.journal_one.carousel.get_items()[0]

        self.assertEqual(expected, result)

    def test_latest_articles_limit(self):
        carousel = models.Carousel.objects.create(
            latest_articles=True,
            article_limit=1,
        )
        self.journal_one.carousel = carousel
        self.journal_one.save()

        self.assertEqual(1, len(self.journal_one.carousel.get_items()))

    def test_press_latest_articles(self):
        carousel = models.Carousel.objects.create(latest_articles=True)
        self.press.carousel = carousel
        self.press.save()
        carousel_items = [item.pk for item in self.press.carousel.get_items()]
        expected = [self.article_two.pk, self.article_one.pk]
        self.assertEqual(expected, carousel_items)

    def test_press_latest_articles_excludes_hidden(self):
        carousel = models.Carousel.objects.create(latest_articles=True)
        self.press.carousel = carousel
        self.press.save()
        carousel_items = [item.pk for item in self.press.carousel.get_items()]
        self.assertNotIn(self.hidden_article.pk, carousel_items)

    def test_selected_articles(self):
        carousel = models.Carousel.objects.create(latest_articles=False)
        article = sm_models.Article.objects.create(
            stage=sm_models.STAGE_PUBLISHED,
            date_published=self.article_two.date_published + relativedelta(years=1),
        )
        carousel.articles.add(article)
        self.journal_one.carousel = carousel
        self.journal_one.save()

        expected = [article]
        result = list(self.journal_one.carousel.get_items())

        self.assertListEqual(expected, result)

    def test_latest_news(self):
        carousel = models.Carousel.objects.create(latest_articles=True)
        self.journal_one.carousel = carousel
        self.journal_one.save()
        expected = self.article_two
        result = self.journal_one.carousel.get_items()[0]

        self.assertEqual(expected, result)

    def test_selected_news(self):
        carousel = models.Carousel.objects.create(latest_articles=False)
        news_item = comms_models.NewsItem.objects.create(
            posted=FROZEN_DATETIME_20180628,
        )
        carousel.news_articles.add(news_item)
        self.journal_one.carousel = carousel
        self.journal_one.save()

        expected = [news_item]
        result = list(self.journal_one.carousel.get_items())

        self.assertListEqual(expected, result)
