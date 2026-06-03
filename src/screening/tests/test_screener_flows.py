__copyright__ = "Copyright 2026 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

import datetime

from django.test import TestCase
from django.urls import reverse

from screening import logic as screening_logic, models as screening_models
from submission import models as submission_models
from utils.testing import helpers


class ScreenerFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.screener = helpers.create_user(
            "screener-flows@example.org",
            roles=["editor"],
            journal=cls.journal_one,
        )
        cls.screener.is_active = True
        cls.screener.save()
        cls.other_user = helpers.create_user(
            "other-flows@example.org",
            roles=["author"],
            journal=cls.journal_one,
        )
        cls.other_user.is_active = True
        cls.other_user.save()
        cls.editor = helpers.create_user(
            "editor-flows@example.org",
            roles=["editor"],
            journal=cls.journal_one,
        )
        cls.author = helpers.create_user(
            "author-flows@example.org",
            roles=["author"],
            journal=cls.journal_one,
        )
        cls.article = submission_models.Article.objects.create(
            journal=cls.journal_one,
            title="Screener-side Flow Article",
            stage=submission_models.STAGE_SCREENING,
            owner=cls.author,
            correspondence_author=cls.author,
        )
        cls.round = screening_models.ScreeningRound.objects.create(
            article=cls.article,
            round_number=1,
        )
        cls.assignment = screening_models.ScreeningAssignment.objects.create(
            article=cls.article,
            screener=cls.screener,
            editor=cls.editor,
            screening_round=cls.round,
            date_due=datetime.date.today() + datetime.timedelta(days=10),
        )
        cls.screening_form = screening_models.ScreeningForm.objects.create(
            journal=cls.journal_one,
            name="Default Screening Form",
            intro="",
            thanks="",
        )
        cls.assignment.form = cls.screening_form
        cls.assignment.save()
        cls.form_element = screening_models.ScreeningFormElement.objects.create(
            name="General comments",
            kind="textarea",
            required=True,
            order=1,
        )
        cls.screening_form.elements.add(cls.form_element)

    def test_pending_list_visible_to_screener(self):
        self.client.force_login(self.screener)
        response = self.client.get(
            reverse("screening_requests"),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.article.title)

    def test_accept_records_date_accepted(self):
        self.client.force_login(self.screener)
        self.client.post(
            reverse(
                "accept_screening_request",
                kwargs={"assignment_id": self.assignment.pk},
            ),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assignment.refresh_from_db()
        self.assertIsNotNone(self.assignment.date_accepted)

    def test_decline_records_date_declined(self):
        self.client.force_login(self.screener)
        self.client.post(
            reverse(
                "decline_screening_request",
                kwargs={"assignment_id": self.assignment.pk},
            ),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assignment.refresh_from_db()
        self.assertIsNotNone(self.assignment.date_declined)

    def test_decline_blocked_after_complete(self):
        self.assignment.is_complete = True
        self.assignment.save()
        self.client.force_login(self.screener)
        self.client.post(
            reverse(
                "decline_screening_request",
                kwargs={"assignment_id": self.assignment.pk},
            ),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assignment.refresh_from_db()
        self.assertIsNone(self.assignment.date_declined)

    def test_other_user_cannot_access_assignment(self):
        self.client.force_login(self.other_user)
        response = self.client.get(
            reverse(
                "do_screening",
                kwargs={"assignment_id": self.assignment.pk},
            ),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(response.status_code, 404)

    def test_do_screening_get_renders(self):
        self.client.force_login(self.screener)
        response = self.client.get(
            reverse(
                "do_screening",
                kwargs={"assignment_id": self.assignment.pk},
            ),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Recommendation")

    def test_do_screening_post_completes_assignment(self):
        self.client.force_login(self.screener)
        response = self.client.post(
            reverse(
                "do_screening",
                kwargs={"assignment_id": self.assignment.pk},
            ),
            {
                str(self.form_element.pk): "Looks suitable for peer review.",
                "recommendation": "accept_for_peer_review",
                "suggested_reviewers": "Dr. Smith",
                "comments_for_editor": "Strong submission.",
            },
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(response.status_code, 302)
        self.assignment.refresh_from_db()
        self.assertTrue(self.assignment.is_complete)
        self.assertEqual(
            self.assignment.recommendation,
            "accept_for_peer_review",
        )
        self.assertIsNotNone(self.assignment.date_complete)

    def test_do_screening_blocks_declined_assignment(self):
        self.assignment.date_declined = datetime.datetime.now()
        self.assignment.save()
        self.client.force_login(self.screener)
        response = self.client.get(
            reverse(
                "do_screening",
                kwargs={"assignment_id": self.assignment.pk},
            ),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(response.status_code, 404)

    def test_thanks_visible_to_screener(self):
        self.client.force_login(self.screener)
        response = self.client.get(
            reverse(
                "screening_thanks",
                kwargs={"assignment_id": self.assignment.pk},
            ),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.article.title)

    def test_screening_form_answer_persisted_after_submission(self):
        self.client.force_login(self.screener)
        self.client.post(
            reverse(
                "do_screening",
                kwargs={"assignment_id": self.assignment.pk},
            ),
            {
                str(self.form_element.pk): "Reasonable submission.",
                "recommendation": "revisions_required",
            },
            SERVER_NAME=self.journal_one.domain,
        )
        answer = screening_models.ScreeningAssignmentAnswer.objects.get(
            assignment=self.assignment,
        )
        self.assertEqual(answer.answer, "Reasonable submission.")
