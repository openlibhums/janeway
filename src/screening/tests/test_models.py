__copyright__ = "Copyright 2026 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

import datetime

from django.test import TestCase

from screening import models as screening_models
from submission import models as submission_models
from utils.testing import helpers


class ScreeningModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.author = helpers.create_user(
            "screening-author@example.org",
            roles=["author"],
            journal=cls.journal_one,
        )
        cls.screener_one = helpers.create_user(
            "screener-one@example.org",
            roles=["editor"],
            journal=cls.journal_one,
        )
        cls.screener_two = helpers.create_user(
            "screener-two@example.org",
            roles=["editor"],
            journal=cls.journal_one,
        )
        cls.editor = helpers.create_user(
            "screening-editor@example.org",
            roles=["editor"],
            journal=cls.journal_one,
        )
        cls.article = submission_models.Article.objects.create(
            journal=cls.journal_one,
            title="A Screening Test Article",
            stage=submission_models.STAGE_SCREENING,
            owner=cls.author,
            correspondence_author=cls.author,
        )
        cls.round = screening_models.ScreeningRound.objects.create(
            article=cls.article,
            round_number=1,
        )
        cls.assignment_anonymous = screening_models.ScreeningAssignment.objects.create(
            article=cls.article,
            screener=cls.screener_one,
            editor=cls.editor,
            screening_round=cls.round,
            date_due=datetime.date.today() + datetime.timedelta(days=7),
            anonymous_to_author=True,
            anonymous_to_coscreeners=False,
        )
        cls.assignment_open = screening_models.ScreeningAssignment.objects.create(
            article=cls.article,
            screener=cls.screener_two,
            editor=cls.editor,
            screening_round=cls.round,
            date_due=datetime.date.today() + datetime.timedelta(days=7),
            anonymous_to_author=False,
            anonymous_to_coscreeners=False,
        )

    def test_screening_round_str(self):
        self.assertIn("round_number: 1", str(self.round))

    def test_screening_round_latest_article_round(self):
        latest = screening_models.ScreeningRound.latest_article_round(self.article)
        self.assertEqual(latest, self.round)

    def test_screening_round_unique_per_article_number(self):
        with self.assertRaises(Exception):
            screening_models.ScreeningRound.objects.create(
                article=self.article,
                round_number=1,
            )

    def test_screener_display_hidden_from_author_when_anonymous(self):
        self.assertEqual(
            self.assignment_anonymous.screener_display(viewer=self.author),
            "Anonymous screener",
        )

    def test_screener_display_visible_to_author_when_not_anonymous(self):
        self.assertEqual(
            self.assignment_open.screener_display(viewer=self.author),
            self.screener_two.full_name(),
        )

    def test_screener_display_visible_to_editor_regardless_of_flag(self):
        self.assertEqual(
            self.assignment_anonymous.screener_display(viewer=self.editor),
            self.screener_one.full_name(),
        )

    def test_screener_display_hidden_from_coscreener_when_flag_set(self):
        assignment = screening_models.ScreeningAssignment.objects.create(
            article=self.article,
            screener=self.screener_one,
            editor=self.editor,
            screening_round=self.round,
            date_due=datetime.date.today() + datetime.timedelta(days=7),
            anonymous_to_author=False,
            anonymous_to_coscreeners=True,
        )
        coscreener_assignment = screening_models.ScreeningAssignment.objects.create(
            article=self.article,
            screener=self.screener_two,
            editor=self.editor,
            screening_round=self.round,
            date_due=datetime.date.today() + datetime.timedelta(days=7),
            anonymous_to_author=False,
            anonymous_to_coscreeners=False,
        )
        self.assertEqual(
            assignment.screener_display(viewer=self.screener_two),
            "Anonymous screener",
        )
        self.assertEqual(
            coscreener_assignment.screener_display(viewer=self.screener_one),
            self.screener_two.full_name(),
        )

    def test_screening_assignment_is_late(self):
        late_assignment = screening_models.ScreeningAssignment.objects.create(
            article=self.article,
            screener=self.screener_one,
            editor=self.editor,
            screening_round=self.round,
            date_due=datetime.date.today() - datetime.timedelta(days=1),
        )
        self.assertTrue(late_assignment.is_late)
        self.assertFalse(self.assignment_open.is_late)

    def test_screening_form_str(self):
        form = screening_models.ScreeningForm.objects.create(
            journal=self.journal_one,
            name="Default Screening Form",
            intro="Welcome",
            thanks="Thank you",
        )
        self.assertEqual(str(form), "Default Screening Form")

    def test_screening_revision_request_str(self):
        request = screening_models.ScreeningRevisionRequest.objects.create(
            article=self.article,
            editor=self.editor,
            date_due=datetime.date.today() + datetime.timedelta(days=14),
        )
        self.assertIn("Screening revision", str(request))

    def test_accept_stamps_date_accepted_once(self):
        assignment = screening_models.ScreeningAssignment.objects.create(
            article=self.article,
            screener=self.screener_one,
            editor=self.editor,
            screening_round=self.round,
            date_due=datetime.date.today() + datetime.timedelta(days=7),
        )
        self.assertTrue(assignment.accept())
        first_stamp = assignment.date_accepted
        self.assertIsNotNone(first_stamp)
        self.assertFalse(assignment.accept())
        self.assertEqual(assignment.date_accepted, first_stamp)

    def test_decline_stamps_date_declined_once(self):
        assignment = screening_models.ScreeningAssignment.objects.create(
            article=self.article,
            screener=self.screener_one,
            editor=self.editor,
            screening_round=self.round,
            date_due=datetime.date.today() + datetime.timedelta(days=7),
        )
        self.assertTrue(assignment.decline())
        first_stamp = assignment.date_declined
        self.assertIsNotNone(first_stamp)
        self.assertFalse(assignment.decline())
        self.assertEqual(assignment.date_declined, first_stamp)

    def test_withdraw_is_idempotent(self):
        assignment = screening_models.ScreeningAssignment.objects.create(
            article=self.article,
            screener=self.screener_one,
            editor=self.editor,
            screening_round=self.round,
            date_due=datetime.date.today() + datetime.timedelta(days=7),
        )
        self.assertTrue(assignment.withdraw())
        self.assertTrue(assignment.is_withdrawn)
        self.assertIsNotNone(assignment.date_declined)
        self.assertFalse(assignment.withdraw())

    def test_reset_clears_completion_and_decline_but_keeps_acceptance(self):
        assignment = screening_models.ScreeningAssignment.objects.create(
            article=self.article,
            screener=self.screener_one,
            editor=self.editor,
            screening_round=self.round,
            date_due=datetime.date.today() + datetime.timedelta(days=7),
        )
        assignment.accept()
        assignment.complete(recommendation="accept_for_peer_review")
        accepted = assignment.date_accepted
        assignment.reset()
        self.assertFalse(assignment.is_complete)
        self.assertIsNone(assignment.date_complete)
        self.assertIsNone(assignment.recommendation)
        self.assertIsNone(assignment.date_declined)
        self.assertEqual(assignment.date_accepted, accepted)

    def test_complete_sets_full_recommendation_payload(self):
        assignment = screening_models.ScreeningAssignment.objects.create(
            article=self.article,
            screener=self.screener_one,
            editor=self.editor,
            screening_round=self.round,
            date_due=datetime.date.today() + datetime.timedelta(days=7),
        )
        assignment.complete(
            recommendation="accept_for_peer_review",
            suggested_reviewers="Dr. Smith",
            comments_for_editor="Strong submission.",
        )
        self.assertTrue(assignment.is_complete)
        self.assertEqual(assignment.recommendation, "accept_for_peer_review")
        self.assertEqual(assignment.suggested_reviewers, "Dr. Smith")
        self.assertEqual(assignment.comments_for_editor, "Strong submission.")
        self.assertIsNotNone(assignment.date_complete)

    def test_revision_cancel_stamps_date_cancelled(self):
        revision = screening_models.ScreeningRevisionRequest.objects.create(
            article=self.article,
            editor=self.editor,
            date_due=datetime.date.today() + datetime.timedelta(days=14),
        )
        revision.cancel()
        self.assertIsNotNone(revision.date_cancelled)
        self.assertTrue(revision.is_cancelled)
        self.assertFalse(revision.is_open)

    def test_revision_complete_opens_new_round(self):
        revision = screening_models.ScreeningRevisionRequest.objects.create(
            article=self.article,
            editor=self.editor,
            date_due=datetime.date.today() + datetime.timedelta(days=14),
        )
        prior_max = (
            screening_models.ScreeningRound.objects.filter(
                article=self.article,
            )
            .order_by("-round_number")
            .first()
            .round_number
        )
        new_round = revision.complete()
        self.assertIsNotNone(revision.date_completed)
        self.assertTrue(revision.is_complete)
        self.assertEqual(new_round.round_number, prior_max + 1)

    def test_open_for_article_returns_only_open(self):
        manager = screening_models.ScreeningRevisionRequest.objects
        self.assertIsNone(manager.open_for_article(self.article))
        first = manager.create(
            article=self.article,
            editor=self.editor,
            date_due=datetime.date.today() + datetime.timedelta(days=14),
        )
        self.assertEqual(manager.open_for_article(self.article), first)
        first.cancel()
        self.assertIsNone(manager.open_for_article(self.article))
