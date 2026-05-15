__copyright__ = "Copyright 2026 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from django.test import TestCase
from django.urls import reverse

from core import logic as core_logic, models as core_models, workflow
from submission import models as submission_models
from utils.testing import helpers


class ScreeningScaffoldTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()

    def test_stage_screening_constant_is_defined(self):
        self.assertEqual(submission_models.STAGE_SCREENING, "Screening")

    def test_screening_in_element_stages(self):
        self.assertEqual(
            workflow.ELEMENT_STAGES["screening"],
            [submission_models.STAGE_SCREENING],
        )

    def test_screening_in_stages_elements(self):
        self.assertEqual(
            workflow.STAGES_ELEMENTS[submission_models.STAGE_SCREENING],
            "screening",
        )

    def test_screening_in_base_elements(self):
        screening_entry = next(
            entry for entry in core_models.BASE_ELEMENTS if entry["name"] == "screening"
        )
        self.assertEqual(screening_entry["stage"], submission_models.STAGE_SCREENING)
        self.assertEqual(screening_entry["handshake_url"], "screening_list")
        self.assertEqual(screening_entry["jump_url"], "screening_article")

    def test_screening_is_not_in_default_workflow(self):
        names = [
            element.element_name
            for element in self.journal_one.workflow().elements.all()
        ]
        self.assertNotIn("screening", names)

    def test_screening_is_available_to_add(self):
        available = core_logic.get_available_elements(self.journal_one.workflow())
        names = [element["name"] for element in available]
        self.assertIn("screening", names)

    def test_screening_can_be_added_to_workflow(self):
        journal_workflow = self.journal_one.workflow()
        request = helpers.get_request(press=self.press, journal=self.journal_one)
        element = core_logic.handle_element_post(
            journal_workflow,
            "screening",
            request,
        )
        self.assertIsNotNone(element)
        journal_workflow.elements.add(element)
        self.assertTrue(self.journal_one.element_in_workflow("screening"))

    def test_screening_list_url_resolves(self):
        path = reverse("screening_list")
        self.assertIn("/screening/", path)

    def test_screening_article_url_resolves(self):
        path = reverse("screening_article", kwargs={"article_id": 1})
        self.assertIn("/screening/article/1/", path)

    def test_screening_list_404s_when_element_not_enabled(self):
        editor = helpers.create_user(
            "screening-editor@example.org",
            roles=["editor"],
            journal=self.journal_one,
        )
        editor.is_active = True
        editor.save()
        self.client.force_login(editor)
        response = self.client.get(
            reverse("screening_list"),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(response.status_code, 404)
