from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from rest_framework.test import APIClient

from utils.testing import helpers
from core import models as core_models
from submission import models as submission_models


class TestAPI(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal, cls.hidden_journal = helpers.create_journals()
        cls.hidden_journal.hide_from_press = True
        cls.hidden_journal.save()
        cls.staff_member = helpers.create_user(
            username="t.paris@voyager.com",
            roles=["author"],
            journal=cls.journal,
            is_staff=True,
            is_active=True,
        )
        cls.editor = helpers.create_user(
            username="h.kim@voyager.com",
            roles=["editor"],
            journal=cls.journal,
            is_active=True,
        )
        cls.average_user = helpers.create_user(
            "a.redshirt@voyager.com",
            roles=["author"],
            journal=cls.journal,
            is_active=True,
        )
        helpers.create_roles(
            ["journal-manager"],
        )
        cls.hidden_article = helpers.create_article(
            cls.hidden_journal,
            with_author=True,
            title="Article in journal hidden from press",
        )
        cls.hidden_article.stage = submission_models.STAGE_PUBLISHED
        cls.hidden_article.date_published = timezone.now()
        cls.hidden_article.save()
        cls.api_client = APIClient()

    @override_settings(URL_CONFIG="domain")
    def test_staff_member_can_assign_journal_manager_role(self):
        self.api_client.force_authenticate(user=self.staff_member)
        url = self.journal.site_url(
            reverse(
                "accountrole-list",
            )
        )
        journal_manager_role = core_models.Role.objects.get(
            slug="journal-manager",
        )
        self.api_client.post(
            path=url,
            data={
                "user": self.average_user.pk,
                "role": journal_manager_role.pk,
                "journal": self.journal.pk,
            },
            SERVER_NAME=self.journal.domain,
        )
        self.assertTrue(
            self.average_user.check_role(
                self.journal,
                journal_manager_role,
            )
        )

    @override_settings(URL_CONFIG="domain")
    def test_editor_cannot_assign_journal_manager_role(self):
        self.api_client.force_authenticate(user=self.editor)
        url = self.journal.site_url(
            reverse(
                "accountrole-list",
            )
        )
        journal_manager_role = core_models.Role.objects.get(
            slug="journal-manager",
        )
        self.api_client.post(
            path=url,
            data={
                "user": self.average_user.pk,
                "role": journal_manager_role.pk,
                "journal": self.journal.pk,
            },
            SERVER_NAME=self.journal.domain,
        )
        self.assertFalse(
            self.average_user.check_role(
                self.journal,
                journal_manager_role,
            )
        )

    @override_settings(URL_CONFIG="domain")
    def test_press_api_excludes_journal_hidden_from_press(self):
        url = self.press.site_url(reverse("journal-list"))
        response = self.api_client.get(
            url,
            SERVER_NAME=self.press.domain,
        )
        self.assertNotIn(
            self.hidden_journal.pk,
            [journal["pk"] for journal in response.json().get("results", [])],
        )

    @override_settings(URL_CONFIG="domain")
    def test_press_api_excludes_article_in_journal_hidden_from_press(self):
        url = self.press.site_url(reverse("article-list"))
        response = self.api_client.get(
            url,
            SERVER_NAME=self.press.domain,
        )
        self.assertNotIn(
            self.hidden_article.title,
            [article["title"] for article in response.json().get("results", [])],
        )

    @override_settings(URL_CONFIG="domain")
    def test_api_works_at_journal_level_even_if_hidden_from_press(self):
        url = self.hidden_journal.site_url(reverse("article-list"))
        response = self.api_client.get(
            url,
            SERVER_NAME=self.hidden_journal.domain,
        )
        self.assertIn(
            self.hidden_article.title,
            [article["title"] for article in response.json().get("results", [])],
        )
