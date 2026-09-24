__copyright__ = "Copyright 2026 Birkbeck, University of London"
__author__ = "Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.core import mail
from django.test import TestCase, override_settings
from django.shortcuts import reverse
from django.urls.base import clear_script_prefix

from discussion import models
from repository import install as repository_install
from utils.install import update_settings
from utils.testing import helpers


class DiscussionJournalAccessTests(TestCase):
    """
    Regression tests for #5479: editors must be able to alter thread
    participants after a thread has started, and threads with no
    participants must not be accessible to unrelated users.
    """

    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        helpers.create_roles(["editor", "author", "reviewer"])
        cls.editor = helpers.create_editor(
            cls.journal_one,
            is_active=True,
        )
        cls.second_editor = helpers.create_editor(
            cls.journal_one,
            username="second_editor@example.org",
            is_active=True,
        )
        cls.regular_user = helpers.create_user(
            "discussion_participant@example.org",
            is_active=True,
        )
        cls.stranger = helpers.create_user(
            "discussion_stranger@example.org",
            is_active=True,
        )
        cls.article = helpers.create_article(cls.journal_one)
        cls.thread = models.Thread.objects.create(
            article=cls.article,
            owner=cls.editor,
            subject="Test Thread",
        )
        cls.journal_manager = helpers.create_user(
            "discussion_journal_manager@example.org",
            roles=["journal-manager"],
            journal=cls.journal_one,
            is_active=True,
        )
        cls.other_journal_editor = helpers.create_editor(
            cls.journal_two,
            username="other_journal_editor@example.org",
            is_active=True,
        )
        cls.other_article = helpers.create_article(cls.journal_two)
        cls.other_thread = models.Thread.objects.create(
            article=cls.other_article,
            owner=cls.other_journal_editor,
            subject="Other Journal Thread",
        )
        update_settings()
        cls.repo_manager = helpers.create_user(
            "discussion_cross_repo_manager@example.org",
            is_active=True,
        )
        cls.repository, cls.repo_subject = helpers.create_repository(
            cls.press,
            [cls.repo_manager],
            [],
            domain="crosscontext.test.com",
        )
        cls.preprint = helpers.create_preprint(
            cls.repository,
            cls.repo_manager,
            cls.repo_subject,
        )
        cls.preprint_thread = models.Thread.objects.create(
            preprint=cls.preprint,
            owner=cls.repo_manager,
            subject="Cross Context Preprint Thread",
        )

    def setUp(self):
        clear_script_prefix()

    def test_editor_can_add_participant_after_thread_started(self):
        self.client.force_login(self.editor)
        response = self.client.post(
            reverse("discussion_add_participant", kwargs={"thread_id": self.thread.pk}),
            data={"user_id": self.regular_user.pk},
        )
        self.assertEqual(response.status_code, 204)
        self.assertIn(self.regular_user, self.thread.participants.all())
        self.assertTrue(
            self.thread.posts_related.filter(
                is_system_message=True,
                body__contains="added",
            ).exists()
        )

    def test_editor_can_remove_participant(self):
        self.thread.participants.add(self.regular_user)
        self.client.force_login(self.editor)
        response = self.client.post(
            reverse(
                "discussion_remove_participant", kwargs={"thread_id": self.thread.pk}
            ),
            data={"user_id": self.regular_user.pk},
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(self.regular_user, self.thread.participants.all())

    def test_thread_owner_cannot_be_removed(self):
        self.thread.participants.add(self.editor)
        self.client.force_login(self.second_editor)
        response = self.client.post(
            reverse(
                "discussion_remove_participant", kwargs={"thread_id": self.thread.pk}
            ),
            data={"user_id": self.editor.pk},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn(self.editor, self.thread.participants.all())

    def test_participant_cannot_manage_participants(self):
        self.thread.participants.add(self.regular_user)
        self.client.force_login(self.regular_user)
        response = self.client.post(
            reverse("discussion_add_participant", kwargs={"thread_id": self.thread.pk}),
            data={"user_id": self.stranger.pk},
        )
        self.assertEqual(response.status_code, 403)
        self.assertNotIn(self.stranger, self.thread.participants.all())

    def test_stranger_cannot_access_thread_with_no_participants(self):
        self.assertEqual(self.thread.participants.count(), 0)
        self.client.force_login(self.stranger)
        response = self.client.get(
            reverse(
                "discussion_thread_detail_partial",
                kwargs={
                    "object_type": "article",
                    "object_id": self.article.pk,
                    "thread_id": self.thread.pk,
                },
            ),
        )
        self.assertEqual(response.status_code, 403)

    def test_participant_can_access_thread(self):
        self.thread.participants.add(self.regular_user)
        self.client.force_login(self.regular_user)
        response = self.client.get(
            reverse(
                "discussion_thread_detail_partial",
                kwargs={
                    "object_type": "article",
                    "object_id": self.article.pk,
                    "thread_id": self.thread.pk,
                },
            ),
        )
        self.assertEqual(response.status_code, 200)

    def test_non_participant_editor_can_access_thread(self):
        self.client.force_login(self.second_editor)
        response = self.client.get(
            reverse(
                "discussion_thread_detail_partial",
                kwargs={
                    "object_type": "article",
                    "object_id": self.article.pk,
                    "thread_id": self.thread.pk,
                },
            ),
        )
        self.assertEqual(response.status_code, 200)

    def test_add_post_joins_poster_as_participant(self):
        self.client.force_login(self.second_editor)
        response = self.client.post(
            reverse("discussion_add_post", kwargs={"thread_id": self.thread.pk}),
            data={"new_post": "A test reply."},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.second_editor, self.thread.participants.all())

    def test_journal_editor_can_open_invite_search(self):
        self.thread.participants.add(self.regular_user)
        self.client.force_login(self.editor)
        response = self.client.get(
            reverse("discussion_invite_search", kwargs={"thread_id": self.thread.pk}),
        )
        self.assertEqual(response.status_code, 200)
        listed_users = list(response.context["object_list"])
        self.assertIn(self.second_editor, listed_users)
        self.assertNotIn(self.regular_user, listed_users)

    def test_anonymous_user_cannot_access_thread(self):
        response = self.client.get(
            reverse(
                "discussion_thread_detail_partial",
                kwargs={
                    "object_type": "article",
                    "object_id": self.article.pk,
                    "thread_id": self.thread.pk,
                },
            ),
        )
        self.assertEqual(response.status_code, 302)

    def test_editor_cannot_add_participant_to_other_journal_thread(self):
        self.client.force_login(self.editor)
        response = self.client.post(
            reverse(
                "discussion_add_participant",
                kwargs={"thread_id": self.other_thread.pk},
            ),
            data={"user_id": self.regular_user.pk},
        )
        self.assertEqual(response.status_code, 404)
        self.assertNotIn(self.regular_user, self.other_thread.participants.all())

    def test_editor_cannot_remove_participant_from_other_journal_thread(self):
        self.other_thread.participants.add(self.stranger)
        self.client.force_login(self.editor)
        response = self.client.post(
            reverse(
                "discussion_remove_participant",
                kwargs={"thread_id": self.other_thread.pk},
            ),
            data={"user_id": self.stranger.pk},
        )
        self.assertEqual(response.status_code, 404)
        self.assertIn(self.stranger, self.other_thread.participants.all())

    def test_editor_cannot_open_invite_search_for_other_journal_thread(self):
        self.client.force_login(self.editor)
        response = self.client.get(
            reverse(
                "discussion_invite_search",
                kwargs={"thread_id": self.other_thread.pk},
            ),
        )
        self.assertEqual(response.status_code, 404)

    def test_editor_cannot_view_other_journal_thread_detail(self):
        self.client.force_login(self.editor)
        response = self.client.get(
            reverse(
                "discussion_thread_detail_partial",
                kwargs={
                    "object_type": "article",
                    "object_id": self.other_article.pk,
                    "thread_id": self.other_thread.pk,
                },
            ),
        )
        self.assertEqual(response.status_code, 404)

    def test_editor_cannot_manage_preprint_thread_from_journal_site(self):
        self.client.force_login(self.editor)
        response = self.client.post(
            reverse(
                "discussion_add_participant",
                kwargs={"thread_id": self.preprint_thread.pk},
            ),
            data={"user_id": self.regular_user.pk},
        )
        self.assertEqual(response.status_code, 404)
        self.assertNotIn(self.regular_user, self.preprint_thread.participants.all())

    def test_journal_manager_can_access_thread(self):
        self.client.force_login(self.journal_manager)
        response = self.client.get(
            reverse(
                "discussion_thread_detail_partial",
                kwargs={
                    "object_type": "article",
                    "object_id": self.article.pk,
                    "thread_id": self.thread.pk,
                },
            ),
        )
        self.assertEqual(response.status_code, 200)

    def test_journal_manager_sees_thread_in_list(self):
        self.client.force_login(self.journal_manager)
        response = self.client.get(
            reverse(
                "discussion_threads_list_partial",
                kwargs={"object_type": "article", "object_id": self.article.pk},
            ),
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.thread, response.context["threads"])

    def test_journal_manager_can_add_participant(self):
        self.client.force_login(self.journal_manager)
        response = self.client.post(
            reverse(
                "discussion_add_participant",
                kwargs={"thread_id": self.thread.pk},
            ),
            data={"user_id": self.regular_user.pk},
        )
        self.assertEqual(response.status_code, 204)
        self.assertIn(self.regular_user, self.thread.participants.all())

    def test_adding_existing_participant_does_not_repeat_notification(self):
        self.client.force_login(self.editor)
        add_url = reverse(
            "discussion_add_participant",
            kwargs={"thread_id": self.thread.pk},
        )
        self.client.post(add_url, data={"user_id": self.regular_user.pk})
        emails_sent = len(mail.outbox)
        self.assertEqual(emails_sent, 1)
        added_posts = self.thread.posts_related.filter(
            is_system_message=True,
            body__contains="added",
        ).count()

        response = self.client.post(add_url, data={"user_id": self.regular_user.pk})

        self.assertEqual(response.status_code, 204)
        self.assertEqual(len(mail.outbox), emails_sent)
        self.assertEqual(
            self.thread.posts_related.filter(
                is_system_message=True,
                body__contains="added",
            ).count(),
            added_posts,
        )

    def test_stranger_cannot_open_article_threads_page(self):
        self.client.force_login(self.stranger)
        response = self.client.get(
            reverse(
                "discussion_threads",
                kwargs={"object_type": "article", "object_id": self.article.pk},
            ),
        )
        self.assertEqual(response.status_code, 403)

    def test_stranger_cannot_load_article_threads_list(self):
        self.client.force_login(self.stranger)
        response = self.client.get(
            reverse(
                "discussion_threads_list_partial",
                kwargs={"object_type": "article", "object_id": self.article.pk},
            ),
        )
        self.assertEqual(response.status_code, 403)

    def test_participant_can_open_article_threads_page(self):
        self.thread.participants.add(self.regular_user)
        self.client.force_login(self.regular_user)
        response = self.client.get(
            reverse(
                "discussion_threads",
                kwargs={"object_type": "article", "object_id": self.article.pk},
            ),
        )
        self.assertEqual(response.status_code, 200)

    def test_editor_can_open_article_threads_page(self):
        self.client.force_login(self.second_editor)
        response = self.client.get(
            reverse(
                "discussion_threads",
                kwargs={"object_type": "article", "object_id": self.article.pk},
            ),
        )
        self.assertEqual(response.status_code, 200)


class DiscussionRepositoryAccessTests(TestCase):
    """
    Regression tests for #5479 in the repository context: repository
    managers must be able to manage thread participants for preprint
    discussions.
    """

    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        update_settings()
        cls.repo_manager = helpers.create_user(
            "discussion_repo_manager@example.org",
            is_active=True,
        )
        cls.server_name = "repo.test.com"
        cls.repository, cls.subject = helpers.create_repository(
            cls.press,
            [cls.repo_manager],
            [],
            domain=cls.server_name,
        )
        repository_install.load_settings(cls.repository)
        cls.preprint_author = helpers.create_user(
            "discussion_preprint_author@example.org",
            is_active=True,
        )
        cls.stranger = helpers.create_user(
            "discussion_repo_stranger@example.org",
            is_active=True,
        )
        cls.preprint = helpers.create_preprint(
            cls.repository,
            cls.preprint_author,
            cls.subject,
        )
        cls.thread = models.Thread.objects.create(
            preprint=cls.preprint,
            owner=cls.repo_manager,
            subject="Preprint Thread",
        )
        cls.other_repo_manager = helpers.create_user(
            "discussion_other_repo_manager@example.org",
            is_active=True,
        )
        cls.other_repository, cls.other_subject = helpers.create_repository(
            cls.press,
            [cls.other_repo_manager],
            [],
            domain="repo2.test.com",
        )
        cls.other_preprint = helpers.create_preprint(
            cls.other_repository,
            cls.other_repo_manager,
            cls.other_subject,
        )
        cls.other_thread = models.Thread.objects.create(
            preprint=cls.other_preprint,
            owner=cls.other_repo_manager,
            subject="Other Repository Thread",
        )

    def setUp(self):
        clear_script_prefix()

    @override_settings(URL_CONFIG="domain")
    def test_repository_manager_can_add_participant(self):
        self.client.force_login(self.repo_manager)
        response = self.client.post(
            reverse("discussion_add_participant", kwargs={"thread_id": self.thread.pk}),
            data={"user_id": self.preprint_author.pk},
            SERVER_NAME=self.server_name,
        )
        self.assertEqual(response.status_code, 204)
        self.assertIn(self.preprint_author, self.thread.participants.all())

    @override_settings(URL_CONFIG="domain")
    def test_repository_manager_can_remove_participant(self):
        self.thread.participants.add(self.preprint_author)
        self.client.force_login(self.repo_manager)
        response = self.client.post(
            reverse(
                "discussion_remove_participant", kwargs={"thread_id": self.thread.pk}
            ),
            data={"user_id": self.preprint_author.pk},
            SERVER_NAME=self.server_name,
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(self.preprint_author, self.thread.participants.all())

    @override_settings(URL_CONFIG="domain")
    def test_repository_manager_can_open_invite_search(self):
        self.client.force_login(self.repo_manager)
        response = self.client.get(
            reverse("discussion_invite_search", kwargs={"thread_id": self.thread.pk}),
            SERVER_NAME=self.server_name,
        )
        self.assertEqual(response.status_code, 200)

    @override_settings(URL_CONFIG="domain")
    def test_invite_search_limited_to_repository_accounts(self):
        self.client.force_login(self.repo_manager)
        response = self.client.get(
            reverse("discussion_invite_search", kwargs={"thread_id": self.thread.pk}),
            SERVER_NAME=self.server_name,
        )
        listed_users = list(response.context["object_list"])
        self.assertIn(self.preprint_author, listed_users)
        self.assertNotIn(self.stranger, listed_users)

    @override_settings(URL_CONFIG="domain")
    def test_repository_manager_can_create_thread(self):
        self.client.force_login(self.repo_manager)
        response = self.client.post(
            reverse(
                "discussion_create_thread",
                kwargs={"object_type": "preprint", "object_id": self.preprint.pk},
            ),
            data={"subject": "A new preprint thread"},
            SERVER_NAME=self.server_name,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            models.Thread.objects.filter(
                preprint=self.preprint,
                subject="A new preprint thread",
            ).exists()
        )

    @override_settings(URL_CONFIG="domain")
    def test_stranger_cannot_access_preprint_thread(self):
        self.client.force_login(self.stranger)
        response = self.client.get(
            reverse(
                "discussion_thread_detail_partial",
                kwargs={
                    "object_type": "preprint",
                    "object_id": self.preprint.pk,
                    "thread_id": self.thread.pk,
                },
            ),
            SERVER_NAME=self.server_name,
        )
        self.assertEqual(response.status_code, 403)

    @override_settings(URL_CONFIG="domain")
    def test_repository_manager_cannot_manage_other_repository_thread(self):
        self.client.force_login(self.repo_manager)
        response = self.client.post(
            reverse(
                "discussion_add_participant",
                kwargs={"thread_id": self.other_thread.pk},
            ),
            data={"user_id": self.preprint_author.pk},
            SERVER_NAME=self.server_name,
        )
        self.assertEqual(response.status_code, 404)
        self.assertNotIn(
            self.preprint_author,
            self.other_thread.participants.all(),
        )

    @override_settings(URL_CONFIG="domain")
    def test_repository_manager_cannot_open_other_repository_invite_search(self):
        self.client.force_login(self.repo_manager)
        response = self.client.get(
            reverse(
                "discussion_invite_search",
                kwargs={"thread_id": self.other_thread.pk},
            ),
            SERVER_NAME=self.server_name,
        )
        self.assertEqual(response.status_code, 404)

    @override_settings(URL_CONFIG="domain")
    def test_stranger_cannot_open_preprint_threads_page(self):
        self.client.force_login(self.stranger)
        response = self.client.get(
            reverse(
                "discussion_threads",
                kwargs={"object_type": "preprint", "object_id": self.preprint.pk},
            ),
            SERVER_NAME=self.server_name,
        )
        self.assertEqual(response.status_code, 403)

    @override_settings(URL_CONFIG="domain")
    def test_participant_can_open_preprint_threads_page(self):
        self.thread.participants.add(self.preprint_author)
        self.client.force_login(self.preprint_author)
        response = self.client.get(
            reverse(
                "discussion_threads",
                kwargs={"object_type": "preprint", "object_id": self.preprint.pk},
            ),
            SERVER_NAME=self.server_name,
        )
        self.assertEqual(response.status_code, 200)
