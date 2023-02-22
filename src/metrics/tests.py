import datetime
import pytz

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time

from metrics.models import ArticleAccess
from utils import install
from utils.testing import helpers
from utils.shared import clear_cache

class ArticleAccessTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        install.update_settings(management_command=False)

    @override_settings(URL_CONFIG="domain")
    def setUp(self):
        self.article = helpers.create_article(
            self.journal_one,
            with_author=True,
            date_published=datetime.datetime(1988, 4, 24, tzinfo=pytz.UTC),
            stage="Published",
        )
        clear_cache()
        self.article_url = f"/article/id/{self.article.id}"

    def test_article_access_when_view_abstract(self):
        self.client.get(
            self.article_url,
            SERVER_NAME=self.journal_one.domain,
            HTTP_USER_AGENT='Chrome/39.0.2171.95 Safari/537.36',
            follow=True,
        )
        self.assertTrue(
            ArticleAccess.objects.filter(
                article=self.article,
                type="view",
                galley_type=None,
            ).exists(),
            "A 'view' has not been recorded for abstract when no render galley"
        )

    def test_article_access_when_view_render_galley(self):
        galley_type = "html"
        galley = helpers.create_galley(
            self.article, type=galley_type, public=True
        )
        self.article.render_galley = galley
        self.article.save()

        self.client.get(
            self.article_url,
            SERVER_NAME=self.journal_one.domain,
            HTTP_USER_AGENT='Chrome/39.0.2171.95 Safari/537.36',
            follow=True,
        )
        self.assertTrue(
            ArticleAccess.objects.filter(
                article=self.article,
                type="view",
                galley_type=galley_type,
            ).exists(),
            "A 'view' has not been recorded for rendered galley"
        )

    def test_NO_article_access_when_view_non_render_galley(self):
        galley_type = "pdf"
        galley = helpers.create_galley(
            self.article, type=galley_type, public=True
        )
        self.article.save()

        self.client.get(
            self.article_url,
            SERVER_NAME=self.journal_one.domain,
            HTTP_USER_AGENT='Chrome/39.0.2171.95 Safari/537.36',
            follow=True,
        )
        self.assertFalse(
            ArticleAccess.objects.filter(
                article=self.article,
                type="view",
                galley_type=galley_type,
            ).exists(),
            "A 'view' has mistakenly been recorded against a non-render galley"
        )
        self.assertTrue(
            ArticleAccess.objects.filter(
                article=self.article,
                type="view",
                galley_type=None,
            ).exists(),
            "A 'view' has not been recorded for abstract when no render galley"
        )

    def test_article_access_when_download_galley(self):
        galley_type = "pdf"
        galley = helpers.create_galley(
            self.article, type=galley_type, public=True
        )

        galley_url = f'/article/{self.article.pk}/galley/{galley.pk}/download/'
        self.client.get(
            galley_url,
            SERVER_NAME=self.journal_one.domain,
            HTTP_USER_AGENT='Chrome/39.0.2171.95 Safari/537.36',
            follow=True,
        )
        self.assertTrue(
            ArticleAccess.objects.filter(
                article=self.article,
                type="download",
                galley_type=galley_type,
            ).exists(),
            "No 'download' recorded when downloading PDF galley"
        )
