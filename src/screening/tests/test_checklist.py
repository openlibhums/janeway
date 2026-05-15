__copyright__ = "Copyright 2026 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from django.test import TestCase
from django.urls import reverse

from core import logic as core_logic
from screening import logic as screening_logic, models as screening_models
from submission import models as submission_models
from utils.testing import helpers


class TechnicalChecklistTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.editor = helpers.create_user(
            "checklist-editor@example.org",
            roles=["editor"],
            journal=cls.journal_one,
        )
        cls.editor.is_active = True
        cls.editor.save()
        cls.author = helpers.create_user(
            "checklist-author@example.org",
            roles=["author"],
            journal=cls.journal_one,
        )
        cls.author.is_active = True
        cls.author.save()

        # Enable screening on journal_one.
        journal_workflow = cls.journal_one.workflow()
        request = helpers.get_request(press=cls.press, journal=cls.journal_one)
        screening_element = core_logic.handle_element_post(
            journal_workflow,
            "screening",
            request,
        )
        journal_workflow.elements.add(screening_element)

        cls.template = screening_models.TechnicalChecklistTemplate.objects.create(
            journal=cls.journal_one,
            name="Default Tech Check",
            is_default=True,
        )
        cls.template_item = (
            screening_models.TechnicalChecklistTemplateItem.objects.create(
                template=cls.template,
                label="Article uploaded in correct format",
                order=1,
            )
        )
        cls.article = submission_models.Article.objects.create(
            journal=cls.journal_one,
            title="Checklist Article",
            stage=submission_models.STAGE_SCREENING,
            owner=cls.author,
            correspondence_author=cls.author,
        )

    def test_ensure_checklist_creates_from_default_template(self):
        checklist = screening_logic.ensure_checklist_for_article(self.article)
        self.assertIsNotNone(checklist)
        self.assertEqual(checklist.items.count(), 1)
        self.assertEqual(
            checklist.items.first().label,
            "Article uploaded in correct format",
        )

    def test_ensure_checklist_idempotent(self):
        first = screening_logic.ensure_checklist_for_article(self.article)
        second = screening_logic.ensure_checklist_for_article(self.article)
        self.assertEqual(first, second)
        self.assertEqual(self.article.technical_checklist.items.count(), 1)

    def test_ensure_checklist_returns_none_without_default_template(self):
        article = submission_models.Article.objects.create(
            journal=self.journal_two,
            title="Other Journal Article",
            stage=submission_models.STAGE_SCREENING,
            owner=self.author,
            correspondence_author=self.author,
        )
        self.assertIsNone(screening_logic.ensure_checklist_for_article(article))

    def test_checklist_templates_list_renders(self):
        self.client.force_login(self.editor)
        response = self.client.get(
            reverse("screening_checklist_templates"),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Default Tech Check")

    def test_create_template(self):
        self.client.force_login(self.editor)
        self.client.post(
            reverse("screening_checklist_templates"),
            {"name": "Second Template"},
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertTrue(
            screening_models.TechnicalChecklistTemplate.objects.filter(
                journal=self.journal_one,
                name="Second Template",
            ).exists()
        )

    def test_add_template_item(self):
        self.client.force_login(self.editor)
        self.client.post(
            reverse(
                "edit_screening_checklist_template",
                kwargs={"template_id": self.template.pk},
            ),
            {
                "item": "1",
                "label": "Anonymised PDF supplied",
                "order": "2",
            },
            SERVER_NAME=self.journal_one.domain,
        )
        self.template.refresh_from_db()
        self.assertEqual(self.template.items.count(), 2)

    def test_toggle_checklist_item(self):
        checklist = screening_logic.ensure_checklist_for_article(self.article)
        item = checklist.items.first()
        self.client.force_login(self.editor)
        self.client.post(
            reverse("toggle_checklist_item", kwargs={"item_id": item.pk}),
            SERVER_NAME=self.journal_one.domain,
        )
        item.refresh_from_db()
        self.assertTrue(item.is_complete)
        self.assertEqual(item.completed_by, self.editor)
        self.assertIsNotNone(item.completed_at)

    def test_toggle_checklist_item_clears_state_on_second_press(self):
        checklist = screening_logic.ensure_checklist_for_article(self.article)
        item = checklist.items.first()
        self.client.force_login(self.editor)
        self.client.post(
            reverse("toggle_checklist_item", kwargs={"item_id": item.pk}),
            SERVER_NAME=self.journal_one.domain,
        )
        self.client.post(
            reverse("toggle_checklist_item", kwargs={"item_id": item.pk}),
            SERVER_NAME=self.journal_one.domain,
        )
        item.refresh_from_db()
        self.assertFalse(item.is_complete)
        self.assertIsNone(item.completed_by)
        self.assertIsNone(item.completed_at)

    def test_save_checklist_item_comment(self):
        checklist = screening_logic.ensure_checklist_for_article(self.article)
        item = checklist.items.first()
        self.client.force_login(self.editor)
        self.client.post(
            reverse("save_checklist_item_comment", kwargs={"item_id": item.pk}),
            {"comment": "Confirmed."},
            SERVER_NAME=self.journal_one.domain,
        )
        item.refresh_from_db()
        self.assertEqual(item.comment, "Confirmed.")

    def test_checklist_panel_visible_on_screening_article_page(self):
        screening_logic.open_screening_round(self.article)
        self.client.force_login(self.editor)
        response = self.client.get(
            reverse(
                "screening_article",
                kwargs={"article_id": self.article.pk},
            ),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Technical Checklist")
        self.assertContains(response, "Article uploaded in correct format")
