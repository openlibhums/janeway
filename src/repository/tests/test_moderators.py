from django.test import override_settings
from django.urls import reverse

from repository import forms
from repository.tests.test_frozen_authors import PreprintFrozenAuthorTestBase
from utils.testing import helpers


@override_settings(URL_CONFIG="domain")
class TestModerators(PreprintFrozenAuthorTestBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.moderator = helpers.create_user("moderator@janeway.systems")
        cls.moderator.is_active = True
        cls.moderator.save()
        cls.repository.moderators.add(cls.moderator)
        cls.press.enable_preprints = True
        cls.press.save()

    def status(self, user, name, args=None):
        self.client.force_login(user)
        response = self.client.get(
            reverse(name, args=args),
            SERVER_NAME=self.repository.domain,
        )
        return response.status_code

    def test_moderators_moderate_but_do_not_configure(self):
        for name, args in (
            ("preprints_manager", None),
            ("repository_manager_article", [self.preprint.pk]),
            ("version_queue", None),
            ("repository_manager_authors", [self.preprint.pk]),
        ):
            with self.subTest(name):
                self.assertEqual(self.status(self.moderator, name, args), 200)
        for name in (
            "repository_subjects",
            "repository_fields",
            "repository_moderators",
        ):
            with self.subTest(name):
                self.assertEqual(self.status(self.moderator, name), 403)
                self.assertEqual(self.status(self.manager, name), 200)

    def test_side_menu_matches_the_role(self):
        for user, configures in ((self.moderator, False), (self.manager, True)):
            with self.subTest(user=user.email):
                self.client.force_login(user)
                response = self.client.get(
                    reverse("preprints_manager"),
                    SERVER_NAME=self.repository.domain,
                )
                self.assertContains(response, reverse("version_queue"))
                self.assertContains(
                    response,
                    reverse("repository_moderators"),
                    count=2 if configures else 0,
                )

    def test_moderators_can_receive_submission_notifications(self):
        form = forms.RepositoryEmails(instance=self.repository, press=self.press)
        self.assertIn(
            self.moderator,
            form.fields["submission_notification_recipients"].queryset,
        )
