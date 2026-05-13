__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Birkbeck Centre for Technology and Publishing"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from press import models as press_models
from repository import models as repo_models
from utils.testing import helpers


@override_settings(
    CAPTCHA_TYPE=None,
    URL_CONFIG="domain",
)
class CommentModerationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = press_models.Press.objects.create(
            name="Test Press",
            domain="testserver",
        )
        cls.manager = helpers.create_user("manager@example.com")
        cls.manager.is_active = True
        cls.manager.save()

        cls.author = helpers.create_user("author@example.com")
        cls.author.is_active = True
        cls.author.save()

        cls.commenter = helpers.create_user("commenter@example.com")
        cls.commenter.is_active = True
        cls.commenter.save()

        cls.repository, cls.subject = helpers.create_repository(
            cls.press,
            [cls.manager],
            [],
            domain="repo.example.com",
        )
        cls.repository.enable_comments = True
        cls.repository.new_comment = (
            "New comment on {{ preprint.title }} for {{ manager.full_name }}"
        )
        cls.repository.comment_published = "Comment published on {{ preprint.title }}"
        cls.repository.comment_approved = (
            "Your comment on {{ preprint.title }} was approved"
        )
        cls.repository.save()

        cls.preprint = helpers.create_preprint(
            repository=cls.repository,
            author=cls.author,
            subject=cls.subject,
        )
        cls.preprint.date_published = timezone.now()
        cls.preprint.save()

    def _make_comment(self, is_reviewed=False, is_public=False):
        return repo_models.Comment.objects.create(
            author=self.commenter,
            preprint=self.preprint,
            body="A test comment.",
            is_reviewed=is_reviewed,
            is_public=is_public,
        )

    def test_new_comment_notifies_managers_not_owner(self):
        self.client.force_login(self.commenter)
        self.client.post(
            reverse("repository_preprint", kwargs={"preprint_id": self.preprint.pk}),
            {"body": "A new comment."},
            SERVER_NAME=self.repository.domain,
        )
        recipients = [m.to[0] for m in mail.outbox]
        self.assertIn(self.manager.email, recipients)
        self.assertNotIn(self.author.email, recipients)

    def test_comment_approval_notifies_owner_and_commenter(self):
        comment = self._make_comment()
        mail.outbox.clear()
        self.client.force_login(self.manager)
        self.client.post(
            reverse("repository_manager_comment_list"),
            {
                "preprint_id": self.preprint.pk,
                "comment_public": comment.pk,
            },
            SERVER_NAME=self.repository.domain,
        )
        recipients = [m.to[0] for m in mail.outbox]
        self.assertIn(self.author.email, recipients)
        self.assertIn(self.commenter.email, recipients)

    def test_comment_approval_does_not_double_notify_owner_who_is_commenter(self):
        comment = repo_models.Comment.objects.create(
            author=self.author,
            preprint=self.preprint,
            body="Owner commenting on own submission.",
        )
        mail.outbox.clear()
        self.client.force_login(self.manager)
        self.client.post(
            reverse("repository_manager_comment_list"),
            {
                "preprint_id": self.preprint.pk,
                "comment_public": comment.pk,
            },
            SERVER_NAME=self.repository.domain,
        )
        owner_emails = [m for m in mail.outbox if self.author.email in m.to]
        self.assertEqual(len(owner_emails), 1)

    def test_making_comment_private_does_not_send_notification(self):
        comment = self._make_comment(is_reviewed=True, is_public=True)
        mail.outbox.clear()
        self.client.force_login(self.manager)
        self.client.post(
            reverse("repository_manager_comment_list"),
            {
                "preprint_id": self.preprint.pk,
                "comment_public": comment.pk,
            },
            SERVER_NAME=self.repository.domain,
        )
        self.assertEqual(len(mail.outbox), 0)

    def test_unapproved_comment_not_visible_on_public_page(self):
        self._make_comment(is_reviewed=False, is_public=False)
        response = self.client.get(
            reverse("repository_preprint", kwargs={"preprint_id": self.preprint.pk}),
            SERVER_NAME=self.repository.domain,
        )
        self.assertNotContains(response, "A test comment.")

    def test_approved_comment_visible_on_public_page(self):
        self._make_comment(is_reviewed=True, is_public=True)
        response = self.client.get(
            reverse("repository_preprint", kwargs={"preprint_id": self.preprint.pk}),
            SERVER_NAME=self.repository.domain,
        )
        self.assertContains(response, "A test comment.")

    def test_manager_can_access_comment_list(self):
        self.client.force_login(self.manager)
        response = self.client.get(
            reverse("repository_manager_comment_list"),
            SERVER_NAME=self.repository.domain,
        )
        self.assertEqual(response.status_code, 200)

    def test_non_manager_cannot_access_comment_list(self):
        self.client.force_login(self.commenter)
        response = self.client.get(
            reverse("repository_manager_comment_list"),
            SERVER_NAME=self.repository.domain,
        )
        self.assertEqual(response.status_code, 403)

    def test_pending_comments_appear_in_queue(self):
        comment = self._make_comment(is_reviewed=False)
        self.client.force_login(self.manager)
        response = self.client.get(
            reverse("repository_manager_comment_list"),
            SERVER_NAME=self.repository.domain,
        )
        self.assertIn(comment, response.context["comments"])

    def test_reviewed_comments_not_in_pending_queue(self):
        comment = self._make_comment(is_reviewed=True, is_public=True)
        self.client.force_login(self.manager)
        response = self.client.get(
            reverse("repository_manager_comment_list"),
            SERVER_NAME=self.repository.domain,
        )
        self.assertNotIn(comment, response.context["comments"])

    def test_reviewed_comments_appear_in_reviewed_view(self):
        comment = self._make_comment(is_reviewed=True, is_public=True)
        self.client.force_login(self.manager)
        response = self.client.get(
            reverse("repository_manager_comment_list_reviewed"),
            SERVER_NAME=self.repository.domain,
        )
        self.assertIn(comment, response.context["comments"])

    def test_filtered_view_scopes_to_preprint(self):
        other_author = helpers.create_user("other@example.com")
        other_author.is_active = True
        other_author.save()
        other_preprint = helpers.create_preprint(
            repository=self.repository,
            author=other_author,
            subject=self.subject,
            title="Another Preprint",
        )
        comment_this = self._make_comment()
        comment_other = repo_models.Comment.objects.create(
            author=self.commenter,
            preprint=other_preprint,
            body="Comment on other preprint.",
        )
        self.client.force_login(self.manager)
        response = self.client.get(
            reverse(
                "repository_manager_comment_list_filtered",
                kwargs={"preprint_id": self.preprint.pk},
            ),
            SERVER_NAME=self.repository.domain,
        )
        self.assertIn(comment_this, response.context["comments"])
        self.assertNotIn(comment_other, response.context["comments"])
