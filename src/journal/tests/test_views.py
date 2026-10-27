__copyright__ = "Copyright 2024 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from core import models as core_models
from submission import models as submission_models
from utils.testing import helpers


class PublishedArticlesListViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.sections = []
        cls.articles = []
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        for section_name in ["Article", "Review", "Comment", "Editorial"]:
            section = helpers.create_section(
                journal=cls.journal_one,
                name=section_name,
            )
            cls.sections.append(section)
            for num in range(1, 16):
                cls.articles.append(
                    helpers.create_article(
                        journal=cls.journal_one,
                        title=f"{section_name} {num}",
                        section=section,
                        stage="Published",
                        date_published=thirty_days_ago,
                    )
                )

    def setUp(self):
        self.client = Client()

    def test_count_no_filters(self):
        data = {}
        response = self.client.get("/articles/", data)
        self.assertIn(
            f"60 results",
            response.content.decode(),
        )

    def test_count_filtered_on_section(self):
        data = {"section__pk": self.sections[0].pk}
        response = self.client.get("/articles/", data)
        self.assertIn(
            f"15 results",
            response.content.decode(),
        )

    def test_counts_match_with_filters(self):
        data = {
            "section__pk": self.sections[0].pk,
        }
        response = self.client.get("/articles/", data)
        self.assertIn(
            f"15 results",
            response.content.decode(),
        )
        self.assertIn(
            f"Article (15)",
            response.content.decode(),
        )


class ArticleDownloadAccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.under_review = helpers.create_article(
            cls.journal_one,
            stage=submission_models.STAGE_UNDER_REVIEW,
        )
        cls.accepted = helpers.create_article(
            cls.journal_one,
            stage=submission_models.STAGE_ACCEPTED,
        )
        xml_file = core_models.File.objects.create(
            article_id=cls.accepted.pk,
            label="XML",
            mime_type="application/xml",
            uuid_filename="article.xml",
        )
        helpers.create_galley(cls.accepted, file_obj=xml_file)

    def download(self, url_name, identifier):
        return self.client.get(
            reverse(
                url_name,
                kwargs={"identifier_type": "id", "identifier": identifier},
            ),
            SERVER_NAME=self.journal_one.domain,
        )

    @override_settings(URL_CONFIG="domain")
    def test_xml_not_served_for_unpublished_article(self):
        response = self.download("serve_article_xml", self.accepted.pk)
        self.assertEqual(response.status_code, 404)

    @override_settings(URL_CONFIG="domain")
    def test_citation_downloads_refused_before_acceptance(self):
        for url_name in ("serve_article_ris", "serve_article_bib"):
            with self.subTest(url_name=url_name):
                response = self.download(url_name, self.under_review.pk)
                self.assertEqual(response.status_code, 403)
