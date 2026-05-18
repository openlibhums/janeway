__copyright__ = "Copyright 2026 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

import datetime

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core import logic as core_logic
from screening import logic as screening_logic, models as screening_models
from screening.const import ScreeningRecommendations as SR
from submission import models as submission_models
from utils.testing import helpers


class ScreeningEditorManagementTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.editor = helpers.create_user(
            "editor-mgmt@example.org",
            roles=["editor"],
            journal=cls.journal_one,
        )
        cls.editor.is_active = True
        cls.editor.save()
        cls.screener = helpers.create_user(
            "screener-mgmt@example.org",
            roles=["editor"],
            journal=cls.journal_one,
        )
        cls.screener.is_active = True
        cls.screener.save()
        cls.other_user = helpers.create_user(
            "other-mgmt@example.org",
            roles=["author"],
            journal=cls.journal_one,
        )
        cls.other_user.is_active = True
        cls.other_user.save()
        cls.author = helpers.create_user(
            "author-mgmt@example.org",
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

        cls.article = submission_models.Article.objects.create(
            journal=cls.journal_one,
            title="Editor Management Article",
            stage=submission_models.STAGE_SCREENING,
            owner=cls.author,
            correspondence_author=cls.author,
        )
        cls.round = screening_logic.open_screening_round(cls.article)
        cls.assignment = screening_models.ScreeningAssignment.objects.create(
            article=cls.article,
            screener=cls.screener,
            editor=cls.editor,
            screening_round=cls.round,
            date_due=datetime.date.today() + datetime.timedelta(days=10),
        )

    def test_editor_can_view_edit_assignment_page(self):
        self.client.force_login(self.editor)
        response = self.client.get(
            reverse(
                "edit_screening_assignment",
                kwargs={
                    "article_id": self.article.pk,
                    "assignment_id": self.assignment.pk,
                },
            ),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Edit Screening Assignment")

    def test_editor_can_change_due_date(self):
        new_due = datetime.date.today() + datetime.timedelta(days=30)
        self.client.force_login(self.editor)
        self.client.post(
            reverse(
                "edit_screening_assignment",
                kwargs={
                    "article_id": self.article.pk,
                    "assignment_id": self.assignment.pk,
                },
            ),
            {
                "screener": str(self.screener.pk),
                "date_due": new_due.isoformat(),
                "anonymous_to_author": "on",
            },
            SERVER_NAME=self.journal_one.domain,
        )
        self.assignment.refresh_from_db()
        self.assertEqual(self.assignment.date_due, new_due)

    def test_withdraw_sets_assignment_withdrawn(self):
        self.client.force_login(self.editor)
        self.client.post(
            reverse(
                "withdraw_screening_assignment",
                kwargs={
                    "article_id": self.article.pk,
                    "assignment_id": self.assignment.pk,
                },
            ),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assignment.refresh_from_db()
        self.assertEqual(self.assignment.recommendation, SR.WITHDRAWN.value)
        self.assertIsNotNone(self.assignment.date_declined)

    def test_withdraw_emails_screener(self):
        from django.core import mail as django_mail

        django_mail.outbox = []
        self.client.force_login(self.editor)
        self.client.post(
            reverse(
                "withdraw_screening_assignment",
                kwargs={
                    "article_id": self.article.pk,
                    "assignment_id": self.assignment.pk,
                },
            ),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(len(django_mail.outbox), 1)
        self.assertIn(self.screener.email, django_mail.outbox[0].to)

    def test_repeat_withdraw_does_not_double_email(self):
        from django.core import mail as django_mail

        self.assignment.recommendation = SR.WITHDRAWN.value
        self.assignment.save()
        django_mail.outbox = []
        self.client.force_login(self.editor)
        self.client.post(
            reverse(
                "withdraw_screening_assignment",
                kwargs={
                    "article_id": self.article.pk,
                    "assignment_id": self.assignment.pk,
                },
            ),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(len(django_mail.outbox), 0)

    def test_withdraw_rejects_get(self):
        self.client.force_login(self.editor)
        response = self.client.get(
            reverse(
                "withdraw_screening_assignment",
                kwargs={
                    "article_id": self.article.pk,
                    "assignment_id": self.assignment.pk,
                },
            ),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(response.status_code, 405)
        self.assignment.refresh_from_db()
        self.assertIsNone(self.assignment.recommendation)
        self.assertIsNone(self.assignment.date_declined)

    def test_reset_clears_completion_state(self):
        self.assignment.is_complete = True
        self.assignment.date_complete = timezone.now()
        self.assignment.recommendation = SR.ACCEPT_FOR_PEER_REVIEW.value
        self.assignment.save()
        self.client.force_login(self.editor)
        self.client.post(
            reverse(
                "reset_screening_assignment",
                kwargs={
                    "article_id": self.article.pk,
                    "assignment_id": self.assignment.pk,
                },
            ),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assignment.refresh_from_db()
        self.assertFalse(self.assignment.is_complete)
        self.assertIsNone(self.assignment.date_complete)
        self.assertIsNone(self.assignment.recommendation)

    def test_reset_rejects_get(self):
        self.assignment.is_complete = True
        self.assignment.date_complete = timezone.now()
        self.assignment.recommendation = SR.ACCEPT_FOR_PEER_REVIEW.value
        self.assignment.save()
        self.client.force_login(self.editor)
        response = self.client.get(
            reverse(
                "reset_screening_assignment",
                kwargs={
                    "article_id": self.article.pk,
                    "assignment_id": self.assignment.pk,
                },
            ),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(response.status_code, 405)
        self.assignment.refresh_from_db()
        self.assertTrue(self.assignment.is_complete)

    def test_editor_can_submit_on_behalf_via_do_screening(self):
        self.client.force_login(self.editor)
        response = self.client.get(
            reverse("do_screening", kwargs={"assignment_id": self.assignment.pk}),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(response.status_code, 200)

    def test_screener_can_still_access_do_screening(self):
        self.client.force_login(self.screener)
        response = self.client.get(
            reverse("do_screening", kwargs={"assignment_id": self.assignment.pk}),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(response.status_code, 200)

    def test_other_user_cannot_access_do_screening(self):
        self.client.force_login(self.other_user)
        response = self.client.get(
            reverse("do_screening", kwargs={"assignment_id": self.assignment.pk}),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(response.status_code, 404)

    def test_dashboard_passes_screening_counts(self):
        self.client.force_login(self.screener)
        response = self.client.get(
            reverse("core_dashboard"),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Screening Requests")
