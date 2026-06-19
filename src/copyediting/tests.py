from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.shortcuts import reverse
from django.utils import timezone

from copyediting import models
from core import models as core_models
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


class TestEditorShortcuts(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.editor = helpers.create_user(
            "shortcut_editor@janeway.systems",
            ["editor"],
            journal=cls.journal_one,
        )
        cls.editor.is_active = True
        cls.editor.save()
        cls.author = helpers.create_user(
            "shortcut_author@janeway.systems",
            ["author"],
            journal=cls.journal_one,
        )
        cls.author.is_active = True
        cls.author.save()

        cls.article = helpers.create_article(
            journal=cls.journal_one,
        )
        cls.article.title = "Shortcut Article"
        cls.article.stage = submission_models.STAGE_EDITOR_COPYEDITING
        cls.article.correspondence_author = cls.author
        cls.article.save()
        cls.author.snapshot_as_author(cls.article)

        cls.article_without_author = helpers.create_article(
            journal=cls.journal_one,
        )
        cls.article_without_author.title = "Authorless Article"
        cls.article_without_author.stage = submission_models.STAGE_EDITOR_COPYEDITING
        cls.article_without_author.save()

        cls.manuscript_file = core_models.File.objects.create(
            article_id=cls.article.pk,
            label="Manuscript",
            uuid_filename="test.docx",
        )
        cls.article.manuscript_files.add(cls.manuscript_file)

        cls.notify_assignment = helpers.create_copyedit_assignment(
            article=cls.article,
            copyeditor=cls.editor,
            editor=cls.editor,
            notified=True,
            decision="accept",
            date_decided=timezone.now(),
            copyeditor_completed=timezone.now(),
        )
        cls.notify_review = helpers.create_author_review(
            assignment=cls.notify_assignment,
            author=cls.author,
        )

        cls.skip_assignment = helpers.create_copyedit_assignment(
            article=cls.article,
            copyeditor=cls.editor,
            editor=cls.editor,
            notified=True,
            decision="accept",
            date_decided=timezone.now(),
            copyeditor_completed=timezone.now(),
        )
        cls.skip_review = helpers.create_author_review(
            assignment=cls.skip_assignment,
            author=cls.author,
        )

        cls.replace_assignment = helpers.create_copyedit_assignment(
            article=cls.article,
            copyeditor=cls.editor,
            editor=cls.editor,
            notified=True,
            decision="accept",
            date_decided=timezone.now(),
            copyeditor_completed=timezone.now(),
        )
        cls.replace_assignment.files_for_copyediting.add(cls.manuscript_file)
        cls.replace_assignment.copyeditor_files.add(cls.manuscript_file)
        cls.replace_review = helpers.create_author_review(
            assignment=cls.replace_assignment,
            author=cls.author,
        )

        cls.fixture_assignment_pks = [
            cls.notify_assignment.pk,
            cls.skip_assignment.pk,
            cls.replace_assignment.pk,
        ]

        cls.upload_url = reverse(
            "copyedit_upload_editor_version",
            kwargs={"article_id": cls.article.pk},
        )
        cls.request_author_url = reverse(
            "copyedit_request_author_version",
            kwargs={"article_id": cls.article.pk},
        )

    def test_upload_editor_version_get_renders_form(self):
        self.client.force_login(self.editor)
        response = self.client.get(self.upload_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "upload-editor-version-modal")
        self.assertContains(response, "Upload Editor Version")

    def test_upload_editor_version_creates_complete_assignment(self):
        self.client.force_login(self.editor)
        response = self.client.post(
            self.upload_url,
            {
                "label": "Copyedited Manuscript",
                "file": SimpleUploadedFile(
                    "copyedited.docx",
                    b"copyedited content",
                ),
            },
        )
        assignment = (
            models.CopyeditAssignment.objects.filter(
                article=self.article,
                copyeditor=self.editor,
                editor=self.editor,
            )
            .exclude(pk__in=self.fixture_assignment_pks)
            .get()
        )
        self.assertEqual(
            assignment.copyeditor_files.get().label,
            "Copyedited Manuscript",
        )
        self.assertEqual(assignment.decision, "accept")
        self.assertTrue(assignment.notified)
        self.assertIsNotNone(assignment.date_decided)
        self.assertIsNotNone(assignment.copyeditor_completed)
        self.assertTrue(assignment.actions_available())
        self.assertEqual(
            response["HX-Redirect"],
            reverse(
                "editor_review",
                kwargs={
                    "article_id": self.article.pk,
                    "copyedit_id": assignment.pk,
                },
            ),
        )

    def test_upload_editor_version_requires_file(self):
        self.client.force_login(self.editor)
        assignment_count = models.CopyeditAssignment.objects.filter(
            article=self.article,
        ).count()
        response = self.client.post(
            self.upload_url,
            {"label": "Copyedited Manuscript"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("HX-Redirect", response)
        self.assertContains(response, "This field is required")
        self.assertEqual(
            models.CopyeditAssignment.objects.filter(article=self.article).count(),
            assignment_count,
        )

    def test_request_author_version_creates_assignment_and_review(self):
        self.client.force_login(self.editor)
        response = self.client.post(
            self.request_author_url,
            {"files": [self.manuscript_file.pk]},
        )
        assignment = (
            models.CopyeditAssignment.objects.filter(
                article=self.article,
                copyeditor=self.editor,
                editor=self.editor,
                files_for_copyediting=self.manuscript_file,
            )
            .exclude(pk__in=self.fixture_assignment_pks)
            .get()
        )
        self.assertEqual(assignment.decision, "accept")
        self.assertIsNotNone(assignment.copyeditor_completed)
        self.assertIn(
            self.manuscript_file,
            assignment.copyeditor_files.all(),
        )
        author_review = models.AuthorReview.objects.get(assignment=assignment)
        self.assertEqual(author_review.author, self.author)
        self.assertFalse(author_review.notified)
        self.assertEqual(
            response["HX-Redirect"],
            reverse(
                "request_author_copyedit",
                kwargs={
                    "article_id": self.article.pk,
                    "copyedit_id": assignment.pk,
                    "author_review_id": author_review.pk,
                },
            ),
        )

    def test_request_author_version_without_correspondence_author(self):
        self.client.force_login(self.editor)
        url = reverse(
            "copyedit_request_author_version",
            kwargs={"article_id": self.article_without_author.pk},
        )
        response = self.client.get(url)
        self.assertContains(
            response,
            "does not have a correspondence author",
        )
        self.client.post(url, {"files": [self.manuscript_file.pk]})
        self.assertFalse(
            models.CopyeditAssignment.objects.filter(
                article=self.article_without_author,
            ).exists()
        )

    def test_notify_author_version_send(self):
        self.client.force_login(self.editor)
        response = self.client.post(
            reverse(
                "request_author_copyedit",
                kwargs={
                    "article_id": self.article.pk,
                    "copyedit_id": self.notify_assignment.pk,
                    "author_review_id": self.notify_review.pk,
                },
            ),
            {
                "subject": "New Version Requested",
                "body": "<p>Please upload a new version.</p>",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.author.email, mail.outbox[0].to)
        self.notify_review.refresh_from_db()
        self.assertTrue(self.notify_review.notified)

    def test_notify_author_version_skip(self):
        self.client.force_login(self.editor)
        response = self.client.post(
            reverse(
                "request_author_copyedit",
                kwargs={
                    "article_id": self.article.pk,
                    "copyedit_id": self.skip_assignment.pk,
                    "author_review_id": self.skip_review.pk,
                },
            ),
            {
                "subject": "New Version Requested",
                "body": "<p>Please upload a new version.</p>",
                "skip": "skip",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 0)
        self.skip_review.refresh_from_db()
        self.assertFalse(self.skip_review.notified)

    def test_author_can_replace_file_after_request(self):
        self.client.force_login(self.author)
        response = self.client.post(
            reverse(
                "author_update_file",
                kwargs={
                    "article_id": self.article.pk,
                    "author_review_id": self.replace_review.pk,
                    "file_id": self.manuscript_file.pk,
                },
            ),
            {
                "replacement": "replacement",
                "label": "Author Version",
                "replacement-file": SimpleUploadedFile(
                    "new_version.docx",
                    b"new version content",
                ),
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertNotIn(
            self.manuscript_file,
            self.replace_assignment.copyeditor_files.all(),
        )
        new_file = self.replace_review.files_updated.get()
        self.assertIn(
            new_file,
            self.replace_assignment.copyeditor_files.all(),
        )
        self.assertIn(
            self.manuscript_file,
            self.article.manuscript_files.all(),
        )
