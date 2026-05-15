__copyright__ = "Copyright 2026 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

import datetime

from django.core import mail
from django.test import TestCase
from django.urls import reverse

from core import logic as core_logic
from screening import logic as screening_logic, models as screening_models
from submission import models as submission_models
from utils import install
from utils.testing import helpers


class ScreeningEmailEventTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        install.update_settings(journal_object=cls.journal_one)
        install.update_settings(journal_object=cls.journal_two)
        cls.editor = helpers.create_user(
            "screening-email-editor@example.org",
            roles=["editor"],
            journal=cls.journal_one,
        )
        cls.editor.is_active = True
        cls.editor.save()
        cls.screener = helpers.create_user(
            "screening-email-screener@example.org",
            roles=["editor"],
            journal=cls.journal_one,
        )
        cls.screener.is_active = True
        cls.screener.save()
        cls.author = helpers.create_user(
            "screening-email-author@example.org",
            roles=["author"],
            journal=cls.journal_one,
        )

        journal_workflow = cls.journal_one.workflow()
        request = helpers.get_request(press=cls.press, journal=cls.journal_one)
        screening_element = core_logic.handle_element_post(
            journal_workflow,
            "screening",
            request,
        )
        journal_workflow.elements.add(screening_element)
        for element in journal_workflow.elements.exclude(
            element_name="editor_assignment",
        ):
            element.order += 1
            element.save()
        screening_element.order = 1
        screening_element.save()

        cls.article = submission_models.Article.objects.create(
            journal=cls.journal_one,
            title="Email Event Article",
            stage=submission_models.STAGE_SCREENING,
            owner=cls.author,
            correspondence_author=cls.author,
        )
        cls.round = screening_logic.open_screening_round(cls.article)

    def setUp(self):
        mail.outbox = []

    def test_inviting_screener_sends_invitation_email(self):
        self.client.force_login(self.editor)
        response = self.client.post(
            reverse(
                "add_screening_assignment",
                kwargs={"article_id": self.article.pk, "round_id": self.round.pk},
            ),
            {
                "screener": str(self.screener.pk),
                "date_due": (
                    datetime.date.today() + datetime.timedelta(days=14)
                ).isoformat(),
                "anonymous_to_author": "on",
            },
            SERVER_NAME=self.journal_one.domain,
        )
        # The add view now redirects to the notification preview; the
        # email only goes out when the editor confirms on the preview.
        self.assertEqual(response.status_code, 302)
        assignment = screening_models.ScreeningAssignment.objects.filter(
            article=self.article,
            screener=self.screener,
        ).first()
        self.assertIsNotNone(assignment)
        self.client.post(
            reverse(
                "screening_assignment_notification",
                kwargs={
                    "article_id": self.article.pk,
                    "assignment_id": assignment.pk,
                },
            ),
            {
                "subject": "Screening Invitation",
                "body": "Please screen this article.",
            },
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.screener.email, mail.outbox[0].to)
        self.assertIn("Screening Invitation", mail.outbox[0].subject)

    def test_screening_completion_notifies_editor(self):
        assignment = screening_models.ScreeningAssignment.objects.create(
            article=self.article,
            screener=self.screener,
            editor=self.editor,
            screening_round=self.round,
            date_due=datetime.date.today() + datetime.timedelta(days=10),
        )
        self.client.force_login(self.screener)
        self.client.post(
            reverse("do_screening", kwargs={"assignment_id": assignment.pk}),
            {
                "recommendation": "accept_for_peer_review",
            },
            SERVER_NAME=self.journal_one.domain,
        )
        # mail.outbox accumulates messages across the test client's POST;
        # the screening-complete email is the most recently sent.
        self.assertTrue(any(self.editor.email in message.to for message in mail.outbox))
        completion_email = next(
            message for message in mail.outbox if self.editor.email in message.to
        )
        self.assertIn("Screening Report Complete", completion_email.subject)
