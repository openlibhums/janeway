from django.test import TestCase, override_settings
from django.urls import reverse

from rest_framework.test import APIClient

from utils.testing import helpers
from core import models as core_models


class TestAPI(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal, _ = helpers.create_journals()
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
class TestAccountAPIPermissions(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        helpers.create_roles(["editor", "section-editor", "journal-manager"])
        cls.superuser = helpers.create_user(
            "super@example.com",
            is_superuser=True,
            is_staff=True,
            is_active=True,
        )
        cls.section_editor = helpers.create_user(
            "se@example.com",
            roles=["section-editor"],
            journal=cls.journal_one,
            is_active=True,
        )
        cls.editor = helpers.create_user(
            "editor@example.com",
            roles=["editor"],
            journal=cls.journal_one,
            is_active=True,
        )
        cls.other_manager = helpers.create_user(
            "manager-two@example.com",
            roles=["journal-manager"],
            journal=cls.journal_two,
            is_active=True,
        )
        cls.editor_role = core_models.Role.objects.get(slug="editor")

    def setUp(self):
        self.api_client = APIClient()

    def test_section_editor_cannot_change_account_email(self):
        self.api_client.force_authenticate(user=self.section_editor)
        response = self.api_client.patch(
            reverse("accounts-detail", kwargs={"pk": self.superuser.pk}),
            {"email": "changed@example.com"},
            format="json",
            SERVER_NAME=self.journal_one.domain,
        )
        self.superuser.refresh_from_db()
        self.assertEqual(response.status_code, 405)
        self.assertEqual(self.superuser.email, "super@example.com")

    def test_editor_cannot_delete_account(self):
        self.api_client.force_authenticate(user=self.editor)
        response = self.api_client.delete(
            reverse("accounts-detail", kwargs={"pk": self.other_manager.pk}),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(response.status_code, 405)
        self.assertTrue(
            core_models.Account.objects.filter(pk=self.other_manager.pk).exists()
        )

    def test_section_editor_can_still_search_accounts(self):
        self.api_client.force_authenticate(user=self.section_editor)
        response = self.api_client.get(
            reverse("accounts-list"),
            {"search": "editor@example.com"},
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(response.status_code, 200)

    def test_editor_cannot_add_role_on_another_journal(self):
        self.api_client.force_authenticate(user=self.editor)
        response = self.api_client.post(
            reverse("accountrole-list"),
            {
                "user": self.editor.pk,
                "role": self.editor_role.pk,
                "journal": self.journal_two.pk,
            },
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(self.editor.check_role(self.journal_two, "editor"))

    def test_editor_can_add_role_on_own_journal(self):
        self.api_client.force_authenticate(user=self.editor)
        response = self.api_client.post(
            reverse("accountrole-list"),
            {
                "user": self.section_editor.pk,
                "role": self.editor_role.pk,
                "journal": self.journal_one.pk,
            },
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(self.section_editor.check_role(self.journal_one, "editor"))

    def test_editor_cannot_delete_role_on_another_journal(self):
        account_role = core_models.AccountRole.objects.get(
            user=self.other_manager,
            journal=self.journal_two,
        )
        self.api_client.force_authenticate(user=self.editor)
        response = self.api_client.delete(
            reverse("accountrole-detail", kwargs={"pk": account_role.pk}),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(response.status_code, 404)
        self.assertTrue(
            core_models.AccountRole.objects.filter(pk=account_role.pk).exists()
        )

    def test_editor_cannot_remove_journal_manager_role(self):
        manager = helpers.create_user(
            "manager-one@example.com",
            roles=["journal-manager"],
            journal=self.journal_one,
            is_active=True,
        )
        account_role = core_models.AccountRole.objects.get(
            user=manager,
            journal=self.journal_one,
        )
        self.api_client.force_authenticate(user=self.editor)
        response = self.api_client.delete(
            reverse("accountrole-detail", kwargs={"pk": account_role.pk}),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(
            core_models.AccountRole.objects.filter(pk=account_role.pk).exists()
        )
