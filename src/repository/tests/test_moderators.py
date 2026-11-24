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


@override_settings(URL_CONFIG="domain")
class TestModeratorsPage(PreprintFrozenAuthorTestBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.press.enable_preprints = True
        cls.press.save()
        cls.moderator = helpers.create_user(
            "page_moderator@janeway.systems", first_name="Mona", last_name="Mod"
        )
        cls.repository.moderators.add(cls.moderator)
        cls.candidate = helpers.create_user(
            "candidate@janeway.systems", first_name="Cara", last_name="Candidate"
        )

    def get(self, **params):
        self.client.force_login(self.manager)
        return self.client.get(
            reverse("repository_moderators"),
            params,
            SERVER_NAME=self.repository.domain,
        )

    def post(self, **data):
        self.client.force_login(self.manager)
        return self.client.post(
            reverse("repository_moderators"),
            data,
            SERVER_NAME=self.repository.domain,
        )

    def test_lists_moderators_and_managers_by_default(self):
        accounts = list(self.get().context["account_list"])
        self.assertIn(self.moderator, accounts)
        self.assertIn(self.manager, accounts)
        self.assertNotIn(self.candidate, accounts)

    def test_search_finds_any_account(self):
        response = self.get(search="candidate@janeway.systems")
        self.assertIn(self.candidate, response.context["account_list"])
        self.assertContains(response, "Make moderator")

    def test_filter_to_moderators(self):
        accounts = list(self.get(is_moderator="1").context["account_list"])
        self.assertEqual(accounts, [self.moderator])

    def test_add_and_remove_a_moderator(self):
        response = self.post(
            add_moderator=self.candidate.pk,
            params_string="search=candidate",
        )
        self.assertRedirects(
            response,
            reverse("repository_moderators") + "?search=candidate",
            fetch_redirect_response=False,
        )
        self.assertIn(self.candidate, self.repository.moderators.all())
        self.post(remove_moderator=self.candidate.pk)
        self.assertNotIn(self.candidate, self.repository.moderators.all())
