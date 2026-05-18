__copyright__ = "Copyright 2026 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

import datetime

from django.test import TestCase
from django.urls import reverse

from core import logic as core_logic, models as core_models
from review import models as review_models
from screening import logic as screening_logic, models as screening_models
from submission import models as submission_models
from utils.testing import helpers


class ScreeningFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.editor = helpers.create_user(
            "screening-flow-editor@example.org",
            roles=["editor"],
            journal=cls.journal_one,
        )
        cls.editor.is_active = True
        cls.editor.save()
        cls.section_editor = helpers.create_user(
            "screening-flow-section-editor@example.org",
            roles=["section-editor"],
            journal=cls.journal_one,
        )
        cls.outsider = helpers.create_user(
            "screening-flow-outsider@example.org",
            roles=["author"],
            journal=cls.journal_one,
        )
        cls.author = helpers.create_user(
            "screening-flow-author@example.org",
            roles=["author"],
            journal=cls.journal_one,
        )

        # Enable screening on journal_one's workflow and position it
        # between Editor Assignment and Review so that "next stage" from
        # editor assignment resolves to Screening.
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
            title="Article for Screening Flow",
            stage=submission_models.STAGE_UNASSIGNED,
            owner=cls.author,
            correspondence_author=cls.author,
        )

    def test_open_screening_round_starts_at_one(self):
        new_round = screening_logic.open_screening_round(self.article)
        self.assertEqual(new_round.round_number, 1)

    def test_open_screening_round_increments(self):
        screening_logic.open_screening_round(self.article)
        second = screening_logic.open_screening_round(self.article)
        self.assertEqual(second.round_number, 2)

    def test_eligible_screeners_includes_editorial_team(self):
        pool = screening_logic.eligible_screeners(self.journal_one)
        pool_ids = set(pool.values_list("pk", flat=True))
        self.assertIn(self.editor.pk, pool_ids)
        self.assertIn(self.section_editor.pk, pool_ids)
        self.assertNotIn(self.outsider.pk, pool_ids)

    def test_eligible_screeners_can_exclude_users(self):
        pool = screening_logic.eligible_screeners(
            self.journal_one,
            exclude_user_ids=[self.editor.pk],
        )
        pool_ids = set(pool.values_list("pk", flat=True))
        self.assertNotIn(self.editor.pk, pool_ids)
        self.assertIn(self.section_editor.pk, pool_ids)

    def test_eligible_screeners_uses_pool_when_groups_configured(self):
        """When ScreeningPool.groups is non-empty, only members of those
        editorial groups should be returned — even if there are other
        editors on the journal."""
        group = core_models.EditorialGroup.objects.create(
            name="Screening Pool Group",
            journal=self.journal_one,
            sequence=1,
        )
        group_member = helpers.create_user(
            "screening-pool-member@example.org",
            roles=["author"],
            journal=self.journal_one,
        )
        core_models.EditorialGroupMember.objects.create(
            group=group,
            user=group_member,
            sequence=1,
        )
        pool, _ = screening_models.ScreeningPool.objects.get_or_create(
            journal=self.journal_one,
        )
        pool.groups.add(group)

        pool_qs = screening_logic.eligible_screeners(self.journal_one)
        pool_ids = set(pool_qs.values_list("pk", flat=True))
        self.assertIn(group_member.pk, pool_ids)
        self.assertNotIn(self.editor.pk, pool_ids)
        self.assertNotIn(self.section_editor.pk, pool_ids)

    def test_eligible_screeners_falls_back_when_pool_empty(self):
        """A ScreeningPool with no groups should not constrain the pool
        — the editor/section-editor role fallback applies."""
        screening_models.ScreeningPool.objects.get_or_create(
            journal=self.journal_one,
        )
        pool_qs = screening_logic.eligible_screeners(self.journal_one)
        pool_ids = set(pool_qs.values_list("pk", flat=True))
        self.assertIn(self.editor.pk, pool_ids)
        self.assertIn(self.section_editor.pk, pool_ids)

    def test_assign_screener_creates_assignment_with_anonymity_flags(self):
        screening_round = screening_logic.open_screening_round(self.article)
        assignment, created = screening_logic.assign_screener(
            article=self.article,
            screener=self.section_editor,
            editor=self.editor,
            screening_round=screening_round,
            date_due=datetime.date.today() + datetime.timedelta(days=10),
            anonymous_to_author=True,
            anonymous_to_coscreeners=True,
        )
        self.assertTrue(created)
        self.assertTrue(assignment.anonymous_to_author)
        self.assertTrue(assignment.anonymous_to_coscreeners)

    def test_assign_screener_is_idempotent_per_round(self):
        screening_round = screening_logic.open_screening_round(self.article)
        screening_logic.assign_screener(
            article=self.article,
            screener=self.section_editor,
            editor=self.editor,
            screening_round=screening_round,
            date_due=datetime.date.today() + datetime.timedelta(days=10),
        )
        _, created = screening_logic.assign_screener(
            article=self.article,
            screener=self.section_editor,
            editor=self.editor,
            screening_round=screening_round,
            date_due=datetime.date.today() + datetime.timedelta(days=10),
        )
        self.assertFalse(created)

    def test_move_to_next_stage_routes_to_screening_when_enabled(self):
        review_models.EditorAssignment.objects.create(
            article=self.article,
            editor=self.editor,
            editor_type="editor",
        )
        self.client.force_login(self.editor)
        response = self.client.post(
            reverse(
                "editor_assignment_move_to_next_stage",
                kwargs={"article_id": self.article.pk},
            ),
            SERVER_NAME=self.journal_one.domain,
        )
        self.article.refresh_from_db()
        self.assertEqual(self.article.stage, submission_models.STAGE_SCREENING)
        self.assertTrue(
            screening_models.ScreeningRound.objects.filter(
                article=self.article,
            ).exists()
        )

    def test_move_to_next_stage_routes_to_review_when_screening_disabled(self):
        # journal_two has no screening element; default workflow goes
        # editor_assignment -> review.
        article = submission_models.Article.objects.create(
            journal=self.journal_two,
            title="Article without screening",
            stage=submission_models.STAGE_UNASSIGNED,
            owner=self.author,
            correspondence_author=self.author,
        )
        editor_on_two = helpers.create_user(
            "editor-on-two@example.org",
            roles=["editor"],
            journal=self.journal_two,
        )
        editor_on_two.is_active = True
        editor_on_two.save()
        review_models.EditorAssignment.objects.create(
            article=article,
            editor=editor_on_two,
            editor_type="editor",
        )
        self.client.force_login(editor_on_two)
        self.client.post(
            reverse(
                "editor_assignment_move_to_next_stage",
                kwargs={"article_id": article.pk},
            ),
            SERVER_NAME=self.journal_two.domain,
        )
        article.refresh_from_db()
        self.assertEqual(article.stage, submission_models.STAGE_ASSIGNED)
        self.assertTrue(
            review_models.ReviewRound.objects.filter(article=article).exists()
        )

    def test_move_to_next_stage_requires_editor_assignment(self):
        self.client.force_login(self.editor)
        self.client.post(
            reverse(
                "editor_assignment_move_to_next_stage",
                kwargs={"article_id": self.article.pk},
            ),
            SERVER_NAME=self.journal_one.domain,
        )
        self.article.refresh_from_db()
        self.assertEqual(self.article.stage, submission_models.STAGE_UNASSIGNED)

    def test_add_screening_round_url_creates_round(self):
        self.article.stage = submission_models.STAGE_SCREENING
        self.article.save()
        self.client.force_login(self.editor)
        self.client.post(
            reverse("add_screening_round", kwargs={"article_id": self.article.pk}),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertTrue(
            screening_models.ScreeningRound.objects.filter(
                article=self.article,
            ).exists()
        )

    def test_screening_article_view_renders(self):
        self.article.stage = submission_models.STAGE_SCREENING
        self.article.save()
        screening_logic.open_screening_round(self.article)
        self.client.force_login(self.editor)
        response = self.client.get(
            reverse("screening_article", kwargs={"article_id": self.article.pk}),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Round 1")
        self.assertContains(response, "Screeners")

    def test_add_assignment_view_renders_candidate_table(self):
        """The invitation page renders a table of editorial-team candidates
        with one radio per row, and explains the screener pool in plain
        language."""
        self.article.stage = submission_models.STAGE_SCREENING
        self.article.save()
        screening_round = screening_logic.open_screening_round(self.article)
        self.client.force_login(self.editor)
        response = self.client.get(
            reverse(
                "add_screening_assignment",
                kwargs={
                    "article_id": self.article.pk,
                    "round_id": screening_round.pk,
                },
            ),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(response.status_code, 200)
        # callout text identifying the pool source
        self.assertContains(response, "Screener Pool")
        # at least one radio with name=screener (the section editor)
        self.assertContains(
            response,
            'name="screener"',
        )
        self.assertContains(response, self.section_editor.email)

    def test_add_assignment_view_excludes_already_invited(self):
        """A screener already on the round is dropped from the candidate
        list rendered by the invitation page."""
        self.article.stage = submission_models.STAGE_SCREENING
        self.article.save()
        screening_round = screening_logic.open_screening_round(self.article)
        screening_logic.assign_screener(
            article=self.article,
            screener=self.section_editor,
            editor=self.editor,
            screening_round=screening_round,
            date_due=datetime.date.today() + datetime.timedelta(days=10),
        )
        self.client.force_login(self.editor)
        response = self.client.get(
            reverse(
                "add_screening_assignment",
                kwargs={
                    "article_id": self.article.pk,
                    "round_id": screening_round.pk,
                },
            ),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(response.status_code, 200)
        # The section editor is already on the round so should not appear
        # in the candidate radio column.
        self.assertNotContains(
            response,
            'value="{0}"'.format(self.section_editor.pk),
        )
        # The remaining eligible editor still appears.
        self.assertContains(
            response,
            'value="{0}"'.format(self.editor.pk),
        )

    def test_add_assignment_post_creates_assignment(self):
        """POSTing the invitation form with a candidate pk and the options
        creates a ScreeningAssignment with the chosen options."""
        self.article.stage = submission_models.STAGE_SCREENING
        self.article.save()
        screening_round = screening_logic.open_screening_round(self.article)
        self.client.force_login(self.editor)
        response = self.client.post(
            reverse(
                "add_screening_assignment",
                kwargs={
                    "article_id": self.article.pk,
                    "round_id": screening_round.pk,
                },
            ),
            data={
                "screener": str(self.section_editor.pk),
                "date_due": (
                    datetime.date.today() + datetime.timedelta(days=14)
                ).isoformat(),
                "anonymous_to_author": "on",
            },
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            screening_models.ScreeningAssignment.objects.filter(
                article=self.article,
                screener=self.section_editor,
                screening_round=screening_round,
                anonymous_to_author=True,
            ).exists()
        )

    def test_move_to_next_stage_from_editor_assignment_creates_workflow_log(self):
        """Regression: moving an article from editor_assignment into the
        next stage must create a WorkflowLog entry naming the element
        being entered. On journal_one screening sits immediately after
        editor_assignment, so the log entry must point at the screening
        element. Without it, the Screening stage never appears in the
        article timeline."""
        review_models.EditorAssignment.objects.create(
            article=self.article,
            editor=self.editor,
            editor_type="editor",
        )
        self.client.force_login(self.editor)
        self.client.post(
            reverse(
                "editor_assignment_move_to_next_stage",
                kwargs={"article_id": self.article.pk},
            ),
            SERVER_NAME=self.journal_one.domain,
        )
        log_entry = core_models.WorkflowLog.objects.filter(
            article=self.article,
            element__element_name="screening",
        ).first()
        self.assertIsNotNone(log_entry)
        self.assertEqual(log_entry.user, self.editor)

    def test_move_to_next_stage_from_editor_assignment_logs_review_when_screening_disabled(
        self,
    ):
        """Regression: the same delegation must also produce a
        WorkflowLog entry on journals where screening is not configured,
        in which case the element entered is review."""
        article = submission_models.Article.objects.create(
            journal=self.journal_two,
            title="Article without screening (log)",
            stage=submission_models.STAGE_UNASSIGNED,
            owner=self.author,
            correspondence_author=self.author,
        )
        editor_on_two = helpers.create_user(
            "editor-on-two-log@example.org",
            roles=["editor"],
            journal=self.journal_two,
        )
        editor_on_two.is_active = True
        editor_on_two.save()
        review_models.EditorAssignment.objects.create(
            article=article,
            editor=editor_on_two,
            editor_type="editor",
        )
        self.client.force_login(editor_on_two)
        self.client.post(
            reverse(
                "editor_assignment_move_to_next_stage",
                kwargs={"article_id": article.pk},
            ),
            SERVER_NAME=self.journal_two.domain,
        )
        self.assertTrue(
            core_models.WorkflowLog.objects.filter(
                article=article,
                element__element_name="review",
            ).exists()
        )

    def test_screening_move_to_next_stage_creates_workflow_log(self):
        """Regression: moving an article out of screening must create a
        WorkflowLog entry naming the next element (review on
        journal_one), so the transition is visible in the article
        timeline."""
        self.article.stage = submission_models.STAGE_SCREENING
        self.article.save()
        screening_logic.open_screening_round(self.article)
        self.client.force_login(self.editor)
        self.client.post(
            reverse(
                "screening_move_to_next_stage",
                kwargs={"article_id": self.article.pk},
            ),
            SERVER_NAME=self.journal_one.domain,
        )
        log_entry = core_models.WorkflowLog.objects.filter(
            article=self.article,
            element__element_name="review",
        ).first()
        self.assertIsNotNone(log_entry)
        self.assertEqual(log_entry.user, self.editor)
