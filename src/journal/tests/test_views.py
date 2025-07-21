__copyright__ = "Copyright 2024 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from django.contrib.contenttypes.models import ContentType
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from core import models as core_models
from core.logic import reverse_with_query
from utils.testing import helpers


class JournalViewTestsWithData(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.editor_one = helpers.create_editor(
            cls.journal_one,
            email="editor_jiqjgaysqge1pahnj4xn@example.org",
            first_name="Editor",
            last_name="One",
        )
        cls.editor_two = helpers.create_editor(
            cls.journal_one,
            email="editor_iw9pm21rrrxhm9kp5rfa@example.org",
            first_name="Editor",
            last_name="Two",
        )
        cls.contact_person_one = helpers.create_contact_person(
            cls.editor_one,
            cls.journal_one,
        )
        cls.contact_person_two = helpers.create_contact_person(
            cls.editor_two,
            cls.journal_one,
        )
        cls.journal_content_type = ContentType.objects.get_for_model(cls.journal_one)
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


class PublishedArticlesListViewTests(JournalViewTestsWithData):
    def setUp(self):
        self.client = Client()

    def test_count_no_filters(self):
        data = {}
        response = self.client.get("/articles/", data)
        self.assertIn(
            "60 results",
            response.content.decode(),
        )

    def test_count_filtered_on_section(self):
        data = {"section__pk": self.sections[0].pk}
        response = self.client.get("/articles/", data)
        self.assertIn(
            "15 results",
            response.content.decode(),
        )

    def test_counts_match_with_filters(self):
        data = {
            "section__pk": self.sections[0].pk,
        }
        response = self.client.get("/articles/", data)
        self.assertIn(
            "15 results",
            response.content.decode(),
        )
        self.assertIn(
            "Article (15)",
            response.content.decode(),
        )


class JournalContactTests(JournalViewTestsWithData):
    @override_settings(URL_CONFIG="domain")
    def test_contact_GET(self):
        response = self.client.get(
            reverse("contact"),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(
            self.contact_person_one.account.email,
            response.context["contacts"][0].account.email,
        )
        self.assertEqual(
            [
                (self.editor_one.pk, self.editor_one.full_name()),
                (self.editor_two.pk, self.editor_two.full_name()),
            ],
            response.context["contact_form"].fields["account"].choices,
        )

    @override_settings(URL_CONFIG="domain")
    def test_contact_GET_with_param_for_recipient(self):
        query_params = {
            "recipient": "editor_jiqjgaysqge1pahnj4xn@example.org",
        }
        url = reverse_with_query("contact", query_params=query_params)
        response = self.client.get(url, SERVER_NAME=self.journal_one.domain)
        self.assertEqual(
            self.editor_one.pk,
            response.context["contact_form"].fields["account"].initial,
        )

    @override_settings(URL_CONFIG="domain")
    @override_settings(CAPTCHA_TYPE="")
    def test_contact_POST(self):
        post_data = {
            "account": self.editor_one.pk,
            "sender": "notloggedin@example.org",
            "subject": "Question about submission guidelines",
            "body": "Dear editor, I have a question...",
        }
        self.client.post(
            reverse("contact"),
            post_data,
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertTrue(
            core_models.ContactMessage.objects.filter(
                sender="notloggedin@example.org",
                subject="Question about submission guidelines",
                content_type=self.journal_content_type,
                object_id=self.journal_one.pk,
            ).exists()
        )
