__copyright__ = "Copyright 2026 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

import datetime

from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core import logic as core_logic
from screening import models as screening_models
from submission import models as submission_models
from utils.testing import helpers


class ScreeningRevisionsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.editor = helpers.create_user(
            "revisions-editor@example.org",
            roles=["editor"],
            journal=cls.journal_one,
        )
        cls.editor.is_active = True
        cls.editor.save()
        cls.author = helpers.create_user(
            "revisions-author@example.org",
            roles=["author"],
            journal=cls.journal_one,
        )
        cls.author.is_active = True
        cls.author.save()

        journal_workflow = cls.journal_one.workflow()
        request = helpers.get_request(press=cls.press, journal=cls.journal_one)
        screening_element = core_logic.handle_element_post(
            journal_workflow,
            "screening",
            request,
        )
        journal_workflow.elements.add(screening_element)

        cls.article = submission_models.Article.objects.create(
            journal=cls.journal_one,
            title="Revisions Test Article",
            stage=submission_models.STAGE_SCREENING,
            owner=cls.author,
            correspondence_author=cls.author,
        )

    def setUp(self):
        mail.outbox = []

    def test_editor_can_open_request_revisions_page(self):
        self.client.force_login(self.editor)
        response = self.client.get(
            reverse(
                "request_screening_revisions",
                kwargs={"article_id": self.article.pk},
            ),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Request Revisions")
        self.assertNotContains(response, "open revision request already exists")

    def test_open_revision_blocks_opening_another(self):
        existing = screening_models.ScreeningRevisionRequest.objects.create(
            article=self.article,
            editor=self.editor,
            date_due=datetime.date.today() + datetime.timedelta(days=14),
        )
        self.client.force_login(self.editor)
        response = self.client.get(
            reverse(
                "request_screening_revisions",
                kwargs={"article_id": self.article.pk},
            ),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(
            reverse("view_screening_revision", kwargs={"revision_id": existing.pk}),
            response.url,
        )

    def test_completed_revision_does_not_block_new_request(self):
        screening_models.ScreeningRevisionRequest.objects.create(
            article=self.article,
            editor=self.editor,
            date_due=datetime.date.today() + datetime.timedelta(days=14),
            date_completed=datetime.datetime(2026, 1, 1, 9, 0, 0),
        )
        self.client.force_login(self.editor)
        response = self.client.get(
            reverse(
                "request_screening_revisions",
                kwargs={"article_id": self.article.pk},
            ),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Request Revisions")

    def test_editor_post_creates_revision_request(self):
        self.client.force_login(self.editor)
        due = datetime.date.today() + datetime.timedelta(days=14)
        self.client.post(
            reverse(
                "request_screening_revisions",
                kwargs={"article_id": self.article.pk},
            ),
            {
                "type": "minor_revisions",
                "editor_note": "<p>Please clarify section 3.</p>",
                "date_due": due.isoformat(),
            },
            SERVER_NAME=self.journal_one.domain,
        )
        revision = screening_models.ScreeningRevisionRequest.objects.get(
            article=self.article,
        )
        self.assertEqual(revision.editor, self.editor)
        self.assertEqual(revision.type, "minor_revisions")
        self.assertEqual(revision.date_due, due)

    def test_request_redirects_to_notification_preview(self):
        self.client.force_login(self.editor)
        response = self.client.post(
            reverse(
                "request_screening_revisions",
                kwargs={"article_id": self.article.pk},
            ),
            {
                "type": "minor_revisions",
                "editor_note": "Please revise.",
                "date_due": (
                    datetime.date.today() + datetime.timedelta(days=14)
                ).isoformat(),
            },
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/notify/", response.url)
        # No email sent yet — the editor must confirm on the preview.
        self.assertEqual(len(mail.outbox), 0)

    def test_creating_revision_request_emails_author(self):
        self.client.force_login(self.editor)
        self.client.post(
            reverse(
                "request_screening_revisions",
                kwargs={"article_id": self.article.pk},
            ),
            {
                "type": "minor_revisions",
                "editor_note": "Please revise.",
                "date_due": (
                    datetime.date.today() + datetime.timedelta(days=14)
                ).isoformat(),
            },
            SERVER_NAME=self.journal_one.domain,
        )
        revision = screening_models.ScreeningRevisionRequest.objects.get(
            article=self.article,
        )
        self.client.post(
            reverse(
                "screening_revision_notification",
                kwargs={
                    "article_id": self.article.pk,
                    "revision_id": revision.pk,
                },
            ),
            {
                "subject": "Revisions requested",
                "body": "Please revise as discussed.",
            },
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.author.email, mail.outbox[0].to)

    def test_notification_skip_suppresses_email(self):
        revision = screening_models.ScreeningRevisionRequest.objects.create(
            article=self.article,
            editor=self.editor,
            date_due=datetime.date.today() + datetime.timedelta(days=14),
        )
        self.client.force_login(self.editor)
        self.client.post(
            reverse(
                "screening_revision_notification",
                kwargs={
                    "article_id": self.article.pk,
                    "revision_id": revision.pk,
                },
            ),
            {"skip": "1"},
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(len(mail.outbox), 0)

    def test_other_user_cannot_open_do_revisions(self):
        revision = screening_models.ScreeningRevisionRequest.objects.create(
            article=self.article,
            editor=self.editor,
            date_due=datetime.date.today() + datetime.timedelta(days=14),
        )
        stranger = helpers.create_user(
            "stranger-revisions@example.org",
            roles=["author"],
            journal=self.journal_one,
        )
        stranger.is_active = True
        stranger.save()
        self.client.force_login(stranger)
        response = self.client.get(
            reverse(
                "do_screening_revisions",
                kwargs={"revision_id": revision.pk},
            ),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(response.status_code, 404)

    def test_author_submits_revisions_opens_new_round(self):
        revision = screening_models.ScreeningRevisionRequest.objects.create(
            article=self.article,
            editor=self.editor,
            date_due=datetime.date.today() + datetime.timedelta(days=14),
        )
        self.client.force_login(self.author)
        self.client.post(
            reverse(
                "do_screening_revisions",
                kwargs={"revision_id": revision.pk},
            ),
            {
                "author_note": "Section 3 has been clarified.",
                "submit": "1",
            },
            SERVER_NAME=self.journal_one.domain,
        )
        revision.refresh_from_db()
        self.assertIsNotNone(revision.date_completed)
        self.assertTrue(
            screening_models.ScreeningRound.objects.filter(
                article=self.article,
            ).exists()
        )

    def test_author_completion_emails_editor(self):
        revision = screening_models.ScreeningRevisionRequest.objects.create(
            article=self.article,
            editor=self.editor,
            date_due=datetime.date.today() + datetime.timedelta(days=14),
        )
        self.client.force_login(self.author)
        self.client.post(
            reverse(
                "do_screening_revisions",
                kwargs={"revision_id": revision.pk},
            ),
            {"author_note": "Done.", "submit": "1"},
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.editor.email, mail.outbox[0].to)

    def test_author_can_save_covering_letter_without_submitting(self):
        revision = screening_models.ScreeningRevisionRequest.objects.create(
            article=self.article,
            editor=self.editor,
            date_due=datetime.date.today() + datetime.timedelta(days=14),
        )
        self.client.force_login(self.author)
        self.client.post(
            reverse(
                "do_screening_revisions",
                kwargs={"revision_id": revision.pk},
            ),
            {"author_note": "Saving for later.", "save": "1"},
            SERVER_NAME=self.journal_one.domain,
        )
        revision.refresh_from_db()
        self.assertIsNone(revision.date_completed)
        self.assertIn("Saving for later", revision.author_note or "")

    def test_completed_revision_redirects_author_away(self):
        revision = screening_models.ScreeningRevisionRequest.objects.create(
            article=self.article,
            editor=self.editor,
            date_due=datetime.date.today() + datetime.timedelta(days=14),
            date_completed=datetime.datetime(2026, 1, 1, 9, 0, 0),
        )
        self.client.force_login(self.author)
        response = self.client.get(
            reverse(
                "do_screening_revisions",
                kwargs={"revision_id": revision.pk},
            ),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(
            reverse("view_screening_revision", kwargs={"revision_id": revision.pk}),
            response.url,
        )

    def test_editor_can_view_revision(self):
        revision = screening_models.ScreeningRevisionRequest.objects.create(
            article=self.article,
            editor=self.editor,
            date_due=datetime.date.today() + datetime.timedelta(days=14),
            editor_note="Please tidy section 3.",
        )
        self.client.force_login(self.editor)
        response = self.client.get(
            reverse(
                "view_screening_revision",
                kwargs={"revision_id": revision.pk},
            ),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please tidy section 3")

    def test_editor_can_edit_open_revision(self):
        revision = screening_models.ScreeningRevisionRequest.objects.create(
            article=self.article,
            editor=self.editor,
            date_due=datetime.date.today() + datetime.timedelta(days=14),
            editor_note="Original note.",
        )
        self.client.force_login(self.editor)
        new_due = datetime.date.today() + datetime.timedelta(days=21)
        self.client.post(
            reverse(
                "edit_screening_revisions",
                kwargs={"article_id": self.article.pk, "revision_id": revision.pk},
            ),
            {
                "type": "major_revisions",
                "editor_note": "Updated note.",
                "date_due": new_due.isoformat(),
            },
            SERVER_NAME=self.journal_one.domain,
        )
        revision.refresh_from_db()
        self.assertEqual(revision.type, "major_revisions")
        self.assertEqual(revision.date_due, new_due)
        self.assertIn("Updated note", revision.editor_note)

    def test_editor_can_withdraw_open_revision(self):
        revision = screening_models.ScreeningRevisionRequest.objects.create(
            article=self.article,
            editor=self.editor,
            date_due=datetime.date.today() + datetime.timedelta(days=14),
        )
        self.client.force_login(self.editor)
        self.client.post(
            reverse(
                "withdraw_screening_revisions",
                kwargs={"article_id": self.article.pk, "revision_id": revision.pk},
            ),
            SERVER_NAME=self.journal_one.domain,
        )
        revision.refresh_from_db()
        self.assertIsNotNone(revision.date_cancelled)

    def test_withdraw_revision_emails_author(self):
        revision = screening_models.ScreeningRevisionRequest.objects.create(
            article=self.article,
            editor=self.editor,
            date_due=datetime.date.today() + datetime.timedelta(days=14),
        )
        self.client.force_login(self.editor)
        self.client.post(
            reverse(
                "withdraw_screening_revisions",
                kwargs={"article_id": self.article.pk, "revision_id": revision.pk},
            ),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.author.email, mail.outbox[0].to)

    def test_withdraw_rejects_get(self):
        revision = screening_models.ScreeningRevisionRequest.objects.create(
            article=self.article,
            editor=self.editor,
            date_due=datetime.date.today() + datetime.timedelta(days=14),
        )
        self.client.force_login(self.editor)
        response = self.client.get(
            reverse(
                "withdraw_screening_revisions",
                kwargs={"article_id": self.article.pk, "revision_id": revision.pk},
            ),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(response.status_code, 405)

    def test_withdrawn_revision_does_not_block_new_request(self):
        screening_models.ScreeningRevisionRequest.objects.create(
            article=self.article,
            editor=self.editor,
            date_due=datetime.date.today() + datetime.timedelta(days=14),
            date_cancelled=timezone.now(),
        )
        self.client.force_login(self.editor)
        response = self.client.get(
            reverse(
                "request_screening_revisions",
                kwargs={"article_id": self.article.pk},
            ),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(response.status_code, 200)

    def test_cancelled_revision_redirects_author_away(self):
        revision = screening_models.ScreeningRevisionRequest.objects.create(
            article=self.article,
            editor=self.editor,
            date_due=datetime.date.today() + datetime.timedelta(days=14),
            date_cancelled=timezone.now(),
        )
        self.client.force_login(self.author)
        response = self.client.get(
            reverse(
                "do_screening_revisions",
                kwargs={"revision_id": revision.pk},
            ),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(response.status_code, 302)
