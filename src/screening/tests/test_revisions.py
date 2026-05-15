__copyright__ = "Copyright 2026 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

import datetime

from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

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
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.author.email, mail.outbox[0].to)

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
        uploaded = SimpleUploadedFile(
            "revised.txt",
            b"revised manuscript contents",
            content_type="text/plain",
        )
        self.client.post(
            reverse(
                "do_screening_revisions",
                kwargs={"revision_id": revision.pk},
            ),
            {
                "author_note": "Section 3 has been clarified.",
                "manuscript": uploaded,
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
        self.assertTrue(self.article.manuscript_files.exists())

    def test_author_completion_emails_editor(self):
        revision = screening_models.ScreeningRevisionRequest.objects.create(
            article=self.article,
            editor=self.editor,
            date_due=datetime.date.today() + datetime.timedelta(days=14),
        )
        self.client.force_login(self.author)
        uploaded = SimpleUploadedFile(
            "revised2.txt",
            b"contents",
            content_type="text/plain",
        )
        self.client.post(
            reverse(
                "do_screening_revisions",
                kwargs={"revision_id": revision.pk},
            ),
            {"author_note": "Done.", "manuscript": uploaded},
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.editor.email, mail.outbox[0].to)

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
