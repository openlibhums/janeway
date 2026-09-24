__copyright__ = "Copyright 2025 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from importlib import import_module

from django.apps import apps
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from core import models as core_models
from core import workflow as core_workflow
from submission import models
from utils.testing import helpers
from workflow import logic as workflow_logic


class FrozenAuthorModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.article_one = helpers.create_article(cls.journal_one)
        cls.frozen_author = models.FrozenAuthor.objects.create(
            article=cls.article_one,
            name_prefix="Dr.",
            first_name="S.",
            middle_name="Bella",
            last_name="Rogers",
            name_suffix="Esq.",
        )

    def test_full_name(self):
        self.assertEqual("Dr. S. Bella Rogers Esq.", self.frozen_author.full_name())

    def test_credits(self):
        self.frozen_author.add_credit("conceptualization")
        self.assertEqual(
            self.frozen_author.credits.first().get_role_display(),
            "Conceptualization",
        )


class CreditRecordTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.article_one = helpers.create_article(cls.journal_one)
        cls.frozen_author_one = helpers.create_frozen_author(cls.article_one)

    def test_article_authors_and_credits_for_frozen_author(self):
        role = self.frozen_author_one.add_credit("writing-original-draft")
        expected_frozen_authors = [
            fa for fa, _ in self.article_one.authors_and_credits().items()
        ]
        self.assertEqual(expected_frozen_authors, [self.frozen_author_one])
        expected_roles = [
            roles for _, roles in self.article_one.authors_and_credits().items()
        ]
        self.assertEqual(expected_roles[0].first(), role)


class WorkflowRollbackTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        core_workflow.create_default_workflow(cls.journal_one)
        cls.review_element = core_models.WorkflowElement.objects.get(
            journal=cls.journal_one,
            element_name="review",
        )
        cls.copyediting_element = core_models.WorkflowElement.objects.get(
            journal=cls.journal_one,
            element_name="copyediting",
        )

    def test_rollback_to_review_clears_decision_dates(self):
        article = helpers.create_article(self.journal_one)
        article.stage = models.STAGE_UNDER_REVIEW
        article.save()
        core_models.WorkflowLog.objects.create(
            article=article,
            element=self.review_element,
        )
        article.stage = models.STAGE_ACCEPTED
        article.date_accepted = timezone.now()
        article.save()
        article.stage = models.STAGE_EDITOR_COPYEDITING
        article.save()
        core_models.WorkflowLog.objects.create(
            article=article,
            element=self.copyediting_element,
        )

        workflow_logic.move_to_stage(
            article.stage,
            models.STAGE_UNASSIGNED,
            article,
        )

        article.refresh_from_db()
        self.assertEqual(article.stage, models.STAGE_UNDER_REVIEW)
        self.assertIsNone(article.date_accepted)
        self.assertIsNone(article.date_declined)


class FieldAnswerFieldNameTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.article = helpers.create_article(cls.journal_one)
        cls.field = helpers.create_submission_field(
            cls.journal_one,
            name="Data Availability",
        )
        cls.field_answer = models.FieldAnswer.objects.create(
            field=cls.field,
            article=cls.article,
            answer="Available on request.",
        )

    def test_saving_answer_snapshots_field_name(self):
        self.field_answer.refresh_from_db()
        self.assertEqual(self.field_answer.field_name, "Data Availability")

    def test_renaming_field_updates_answer_field_name(self):
        self.field.name = "Data Access Statement"
        self.field.save()
        self.field_answer.refresh_from_db()
        self.assertEqual(self.field_answer.field_name, "Data Access Statement")

    def test_deleting_field_keeps_answer_name(self):
        self.field.delete()
        self.field_answer.refresh_from_db()
        self.assertIsNone(self.field_answer.field)
        self.assertEqual(self.field_answer.name, "Data Availability")

    def test_saving_answer_without_field_keeps_snapshot(self):
        self.field.delete()
        self.field_answer.refresh_from_db()
        self.field_answer.answer = "Deposited in a repository."
        self.field_answer.save()
        self.field_answer.refresh_from_db()
        self.assertEqual(self.field_answer.field_name, "Data Availability")

    def test_name_prefers_live_field_name(self):
        models.FieldAnswer.objects.filter(pk=self.field_answer.pk).update(
            field_name="Stale Name",
        )
        self.field_answer.refresh_from_db()
        self.assertEqual(self.field_answer.name, "Data Availability")

    def test_migration_populates_field_name_from_field(self):
        models.FieldAnswer.objects.filter(pk=self.field_answer.pk).update(
            field_name="",
        )
        migration = import_module(
            "submission.migrations.0091_populate_fieldanswer_field_name"
        )
        migration.populate_field_answer_field_name(apps, None)
        self.field_answer.refresh_from_db()
        self.assertEqual(self.field_answer.field_name, "Data Availability")
