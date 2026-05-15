__copyright__ = "Copyright 2026 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import TestCase

from core import models as core_models
from core import workflow
from submission import models as submission_models
from utils.testing import helpers


def attach_messages(request):
    setattr(request, "session", {})
    setattr(request, "_messages", FallbackStorage(request))
    return request


class EditorAssignmentWorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.request = helpers.get_request(
            press=cls.press,
            journal=cls.journal_one,
        )

    def test_editor_assignment_is_first_base_element(self):
        self.assertEqual(
            core_models.BASE_ELEMENTS[0]["name"],
            "editor_assignment",
        )
        self.assertEqual(
            core_models.BASE_ELEMENTS[0]["stage"],
            submission_models.STAGE_UNASSIGNED,
        )

    def test_review_element_points_at_stage_assigned(self):
        review_entry = next(
            entry for entry in core_models.BASE_ELEMENTS if entry["name"] == "review"
        )
        self.assertEqual(
            review_entry["stage"],
            submission_models.STAGE_ASSIGNED,
        )

    def test_element_stages_maps_editor_assignment_to_unassigned(self):
        self.assertEqual(
            workflow.ELEMENT_STAGES["editor_assignment"],
            [submission_models.STAGE_UNASSIGNED],
        )

    def test_stages_elements_routes_unassigned_to_editor_assignment(self):
        self.assertEqual(
            workflow.STAGES_ELEMENTS[submission_models.STAGE_UNASSIGNED],
            "editor_assignment",
        )

    def test_default_workflow_starts_with_editor_assignment(self):
        first_element = self.journal_one.workflow().elements.first()
        self.assertEqual(first_element.element_name, "editor_assignment")
        self.assertEqual(first_element.stage, submission_models.STAGE_UNASSIGNED)

    def test_default_workflow_review_element_uses_stage_assigned(self):
        review_element = self.journal_one.workflow().elements.get(
            element_name="review",
        )
        self.assertEqual(review_element.stage, submission_models.STAGE_ASSIGNED)

    def test_default_workflow_includes_five_elements(self):
        elements = list(self.journal_one.workflow().elements.all())
        names = [element.element_name for element in elements]
        self.assertEqual(
            names,
            [
                "editor_assignment",
                "review",
                "copyediting",
                "typesetting",
                "prepublication",
            ],
        )

    def test_editor_assignment_cannot_be_removed(self):
        journal_workflow = self.journal_one.workflow()
        editor_assignment = journal_workflow.elements.get(
            element_name="editor_assignment",
        )
        request = attach_messages(
            helpers.get_request(press=self.press, journal=self.journal_one),
        )
        workflow.remove_element(
            request,
            journal_workflow,
            editor_assignment,
        )
        self.assertTrue(
            journal_workflow.elements.filter(
                element_name="editor_assignment",
            ).exists(),
        )

    def test_set_stage_lands_new_article_in_editor_assignment(self):
        article = submission_models.Article.objects.create(
            journal=self.journal_one,
            title="Workflow ordering test article",
        )
        workflow.set_stage(article)
        article.refresh_from_db()
        self.assertEqual(article.stage, submission_models.STAGE_UNASSIGNED)
        self.assertEqual(
            article.current_workflow_element.element_name,
            "editor_assignment",
        )

    def test_workflow_element_display_name_humanises_snake_case(self):
        editor_assignment = self.journal_one.workflow().elements.get(
            element_name="editor_assignment",
        )
        self.assertEqual(editor_assignment.display_name, "Editor Assignment")

        review_element = self.journal_one.workflow().elements.get(
            element_name="review",
        )
        self.assertEqual(review_element.display_name, "Review")
