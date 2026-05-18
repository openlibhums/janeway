__copyright__ = "Copyright 2026 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

import datetime

from django.test import TestCase
from django.urls import reverse

from core import logic as core_logic, workflow as core_workflow
from review import models as review_models
from screening import logic as screening_logic, models as screening_models
from submission import models as submission_models
from utils.testing import helpers


class ScreeningManagingEditorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.editor = helpers.create_user(
            "screening-me-editor@example.org",
            roles=["editor"],
            journal=cls.journal_one,
        )
        cls.editor.is_active = True
        cls.editor.save()
        cls.author = helpers.create_user(
            "screening-me-author@example.org",
            roles=["author"],
            journal=cls.journal_one,
        )
        # Enable screening on journal_one, placed between editor_assignment
        # and review so that "next stage" from screening resolves to review.
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
            title="Screening Managing Editor Article",
            stage=submission_models.STAGE_SCREENING,
            owner=cls.author,
            correspondence_author=cls.author,
        )
        screening_logic.open_screening_round(cls.article)

    def test_get_next_workflow_element_after_screening_is_review(self):
        next_element = core_workflow.get_next_workflow_element(
            self.journal_one,
            "screening",
        )
        self.assertIsNotNone(next_element)
        self.assertEqual(next_element.element_name, "review")

    def test_get_next_workflow_element_returns_none_when_no_successor(self):
        # On journal_two, screening is not in the workflow at all.
        result = core_workflow.get_next_workflow_element(
            self.journal_two,
            "screening",
        )
        self.assertIsNone(result)

    def test_screening_move_to_next_stage_routes_to_review(self):
        self.client.force_login(self.editor)
        self.client.post(
            reverse(
                "screening_move_to_next_stage",
                kwargs={"article_id": self.article.pk},
            ),
            SERVER_NAME=self.journal_one.domain,
        )
        self.article.refresh_from_db()
        self.assertEqual(self.article.stage, submission_models.STAGE_ASSIGNED)
        self.assertTrue(
            review_models.ReviewRound.objects.filter(article=self.article).exists()
        )

    def test_screening_move_requires_screening_stage(self):
        self.article.stage = submission_models.STAGE_UNASSIGNED
        self.article.save()
        self.client.force_login(self.editor)
        response = self.client.post(
            reverse(
                "screening_move_to_next_stage",
                kwargs={"article_id": self.article.pk},
            ),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(response.status_code, 404)

    def test_screening_move_rejects_get(self):
        self.client.force_login(self.editor)
        response = self.client.get(
            reverse(
                "screening_move_to_next_stage",
                kwargs={"article_id": self.article.pk},
            ),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(response.status_code, 405)

    def test_screening_article_shows_move_and_reject_buttons(self):
        self.client.force_login(self.editor)
        response = self.client.get(
            reverse(
                "screening_article",
                kwargs={"article_id": self.article.pk},
            ),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Move to Review")
        self.assertContains(response, "Reject Article")
