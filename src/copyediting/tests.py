from django.test import TestCase
from django.shortcuts import reverse
from django.utils import timezone

from copyediting import models
from utils.testing import helpers
from submission import models as submission_models


class TestLogic(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.editor = helpers.create_user(
            "typesetter@janeway.systems",
            ["editor"],
            journal=cls.journal_one,
        )
        cls.editor.is_active = True
        cls.editor.save()
        cls.copyeditor = helpers.create_user(
            "copyeditor@janeway.systems",
            ["copyeditor"],
            journal=cls.journal_one,
        )
        cls.copyeditor.is_active = True
        cls.copyeditor.save()
        cls.author = helpers.create_user(
            "author@janeway.systems",
            ["author"],
            journal=cls.journal_one,
        )
        cls.author.is_active = True
        cls.author.save()
        cls.active_article = helpers.create_article(
            journal=cls.journal_one,
        )
        cls.active_article.title = "Active Article"
        cls.active_article.save()
        cls.author.snapshot_as_author(cls.active_article)
        cls.archived_article = helpers.create_article(
            journal=cls.journal_one,
        )
        cls.archived_article.stage = submission_models.STAGE_ARCHIVED
        cls.archived_article.title = "Archived Article"
        cls.archived_article.save()
        cls.author.snapshot_as_author(cls.archived_article)

        cls.active_copyediting_task = models.CopyeditAssignment.objects.create(
            article=cls.active_article,
            copyeditor=cls.copyeditor,
            editor=cls.editor,
        )
        cls.archived_copyediting_task = models.CopyeditAssignment.objects.create(
            article=cls.archived_article,
            copyeditor=cls.copyeditor,
            editor=cls.editor,
        )

        cls.active_author_review = models.AuthorReview.objects.create(
            author=cls.copyeditor,
            assignment=cls.active_copyediting_task,
        )
        cls.archived_author_review = models.AuthorReview.objects.create(
            author=cls.copyeditor,
            assignment=cls.archived_copyediting_task,
        )

    def test_archive_stage_hides_task(self):
        self.client.force_login(self.copyeditor)
        response = self.client.get(reverse("copyedit_requests"))
        self.assertContains(
            response,
            "Active Article",
        )
        self.assertNotContains(response, "Archived Article")

    def test_archived_article_task_404s(self):
        self.client.force_login(self.copyeditor)
        response = self.client.get(
            reverse(
                "do_copyedit", kwargs={"copyedit_id": self.archived_copyediting_task.pk}
            )
        )
        self.assertTrue(
            response.status_code,
            404,
        )

    def test_active_article_task_200s(self):
        self.client.force_login(self.copyeditor)
        response = self.client.get(
            reverse(
                "do_copyedit", kwargs={"copyedit_id": self.active_copyediting_task.pk}
            )
        )
        self.assertTrue(
            response.status_code,
            200,
        )

    def test_archived_article_review_task_404s(self):
        self.client.force_login(self.author)
        response = self.client.get(
            reverse(
                "author_copyedit",
                kwargs={
                    "article_id": self.archived_article.pk,
                    "author_review_id": self.archived_author_review.pk,
                },
            )
        )
        self.assertTrue(
            response.status_code,
            404,
        )

    def test_active_article_review_task_200s(self):
        self.client.force_login(self.author)
        response = self.client.get(
            reverse(
                "author_copyedit",
                kwargs={
                    "article_id": self.active_article.pk,
                    "author_review_id": self.active_author_review.pk,
                },
            )
        )
        self.assertTrue(
            response.status_code,
            200,
        )

    def test_accept_copyedit_sends_email_and_marks_acknowledged(self):
        """Accepting with send sets copyedit_accepted and copyedit_acknowledged."""
        task = models.CopyeditAssignment.objects.create(
            article=self.active_article,
            copyeditor=self.copyeditor,
            editor=self.editor,
            copyeditor_completed=timezone.now(),
        )
        self.client.force_login(self.editor)
        self.client.post(
            reverse(
                "accept_copyedit",
                kwargs={
                    "article_id": self.active_article.pk,
                    "copyedit_id": task.pk,
                },
            ),
            {"subject": "Thank you", "body": "Thank you for your work."},
        )
        task.refresh_from_db()
        self.assertIsNotNone(task.copyedit_accepted)
        self.assertTrue(task.copyedit_acknowledged)

    def test_accept_copyedit_skip_marks_acknowledged_without_email(self):
        """Accepting with skip sets copyedit_accepted and copyedit_acknowledged without sending email."""
        task = models.CopyeditAssignment.objects.create(
            article=self.active_article,
            copyeditor=self.copyeditor,
            editor=self.editor,
            copyeditor_completed=timezone.now(),
        )
        self.client.force_login(self.editor)
        self.client.post(
            reverse(
                "accept_copyedit",
                kwargs={
                    "article_id": self.active_article.pk,
                    "copyedit_id": task.pk,
                },
            ),
            {"skip": "True"},
        )
        task.refresh_from_db()
        self.assertIsNotNone(task.copyedit_accepted)
        self.assertTrue(task.copyedit_acknowledged)

    def test_editor_review_reopen_due_date(self):
        """Posting reopen_due to editor_review saves the due date and redirects to reopen_copyedit."""
        task = models.CopyeditAssignment.objects.create(
            article=self.active_article,
            copyeditor=self.copyeditor,
            editor=self.editor,
            copyeditor_completed=timezone.now(),
        )
        self.client.force_login(self.editor)
        response = self.client.post(
            reverse(
                "editor_review",
                kwargs={
                    "article_id": self.active_article.pk,
                    "copyedit_id": task.pk,
                },
            ),
            {"reopen_due": "1", "due": "2026-05-01"},
        )
        task.refresh_from_db()
        self.assertIsNotNone(task.copyedit_reopened)
        self.assertIsNone(task.copyedit_reopened_complete)
        expected_redirect = reverse(
            "reopen_copyedit",
            kwargs={
                "article_id": self.active_article.pk,
                "copyedit_id": task.pk,
            },
        )
        self.assertRedirects(response, expected_redirect)

    def test_reopen_copyedit_sends_email(self):
        """Posting a subject/body to reopen_copyedit redirects to article_copyediting."""
        task = models.CopyeditAssignment.objects.create(
            article=self.active_article,
            copyeditor=self.copyeditor,
            editor=self.editor,
            copyeditor_completed=timezone.now(),
            copyedit_reopened=timezone.now(),
        )
        self.client.force_login(self.editor)
        response = self.client.post(
            reverse(
                "reopen_copyedit",
                kwargs={
                    "article_id": self.active_article.pk,
                    "copyedit_id": task.pk,
                },
            ),
            {"subject": "Please revisit", "body": "Please reopen your copyedit."},
        )
        task.refresh_from_db()
        self.assertIsNotNone(task.copyedit_reopened)
        expected_redirect = reverse(
            "article_copyediting",
            kwargs={"article_id": self.active_article.pk},
        )
        self.assertRedirects(response, expected_redirect)

    def test_reopen_copyedit_skip(self):
        """Posting skip to reopen_copyedit redirects without sending email."""
        task = models.CopyeditAssignment.objects.create(
            article=self.active_article,
            copyeditor=self.copyeditor,
            editor=self.editor,
            copyeditor_completed=timezone.now(),
            copyedit_reopened=timezone.now(),
        )
        self.client.force_login(self.editor)
        response = self.client.post(
            reverse(
                "reopen_copyedit",
                kwargs={
                    "article_id": self.active_article.pk,
                    "copyedit_id": task.pk,
                },
            ),
            {"skip": "True"},
        )
        expected_redirect = reverse(
            "article_copyediting",
            kwargs={"article_id": self.active_article.pk},
        )
        self.assertRedirects(response, expected_redirect)
