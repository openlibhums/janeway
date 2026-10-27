__copyright__ = "Copyright 2026 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from datetime import timedelta

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from copyediting import models as copyediting_models
from production import models as production_models
from proofing import models as proofing_models
from submission import models as submission_models
from typesetting import models as typesetting_models
from utils import models as utils_models
from utils.testing import helpers


@override_settings(URL_CONFIG="domain")
class ObjectScopingTests(TestCase):
    """
    Workflow objects loaded from the URL must belong to the URL's article,
    or to the current journal where the URL has no article. An editor of
    journal one tries each view with an object from journal two.
    """

    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.editor = helpers.create_editor(cls.journal_one)
        cls.article = helpers.create_article(
            cls.journal_one,
            stage=submission_models.STAGE_UNDER_REVIEW,
        )

        cls.other_editor = helpers.create_editor(
            cls.journal_two,
            email="other_editor@example.com",
        )
        cls.other_article = helpers.create_article(
            cls.journal_two,
            stage=submission_models.STAGE_UNDER_REVIEW,
        )

        # Password reset emails are logged with no target.
        cls.reset_log_entry = utils_models.LogEntry.objects.create(
            types="Reset Token",
            description="https://example.com/reset/secret-token/",
            level="Info",
            is_email=True,
        )
        cls.copyeditor = helpers.create_user(
            "copyeditor@example.com",
            roles=["copyeditor"],
            journal=cls.journal_one,
            is_active=True,
        )
        cls.other_copyeditor = helpers.create_user(
            "other_copyeditor@example.com",
            roles=["copyeditor"],
            journal=cls.journal_one,
            is_active=True,
        )
        cls.other_copyedit = copyediting_models.CopyeditAssignment.objects.create(
            article=cls.other_article,
            copyeditor=cls.other_copyeditor,
            editor=cls.other_editor,
        )
        cls.copyedit = copyediting_models.CopyeditAssignment.objects.create(
            article=cls.article,
            copyeditor=cls.other_copyeditor,
            editor=cls.editor,
        )

        # The proofing manager decorator needs an assignment on the URL article.
        proofing_models.ProofingAssignment.objects.create(
            article=cls.article,
            proofing_manager=cls.editor,
            editor=cls.editor,
        )
        proofing_assignment = proofing_models.ProofingAssignment.objects.create(
            article=cls.other_article,
            proofing_manager=cls.other_editor,
            editor=cls.other_editor,
        )
        proofing_round = proofing_models.ProofingRound.objects.create(
            assignment=proofing_assignment,
        )
        cls.other_proofing_task = proofing_models.ProofingTask.objects.create(
            round=proofing_round,
            proofreader=cls.other_editor,
            due=timezone.now() + timedelta(days=3),
        )
        cls.other_galley = helpers.create_galley(cls.other_article)
        cls.other_proofing_task.galleys_for_proofing.add(cls.other_galley)

        production_assignment = production_models.ProductionAssignment.objects.create(
            article=cls.other_article,
            production_manager=cls.other_editor,
            editor=cls.other_editor,
        )
        cls.other_typeset_task = production_models.TypesetTask.objects.create(
            assignment=production_assignment,
            typesetter=cls.other_editor,
        )

        typesetting_round = typesetting_models.TypesettingRound.objects.create(
            article=cls.other_article,
        )
        cls.other_galley_proofing = typesetting_models.GalleyProofing.objects.create(
            round=typesetting_round,
            manager=cls.other_editor,
            proofreader=cls.other_editor,
            due=timezone.now() + timedelta(days=3),
        )

    def setUp(self):
        self.client.force_login(self.editor)

    def get(self, url_name, **kwargs):
        return self.client.get(
            reverse(url_name, kwargs=kwargs),
            SERVER_NAME=self.journal_one.domain,
        )

    def post(self, url_name, data=None, **kwargs):
        return self.client.post(
            reverse(url_name, kwargs=kwargs),
            data=data or {},
            SERVER_NAME=self.journal_one.domain,
        )

    def test_resend_logged_email_rejects_untargeted_entry(self):
        response = self.get(
            "manage_resend_logged_email",
            article_id=self.article.pk,
            log_id=self.reset_log_entry.pk,
        )
        self.assertEqual(response.status_code, 404)
        self.assertNotContains(
            response,
            "secret-token",
            status_code=404,
        )

    def test_copyediting_views_reject_other_articles_assignment(self):
        for url_name in (
            "notify_copyeditor_assignment",
            "copyedit_edit_assignment",
            "editor_review",
        ):
            with self.subTest(url_name=url_name):
                response = self.get(
                    url_name,
                    article_id=self.article.pk,
                    copyedit_id=self.other_copyedit.pk,
                )
                self.assertEqual(response.status_code, 404)

    def test_copyeditor_cannot_decide_someone_elses_request(self):
        self.client.force_login(self.copyeditor)
        response = self.get(
            "copyedit_request_decision",
            copyedit_id=self.copyedit.pk,
            decision="decline",
        )
        self.assertEqual(response.status_code, 403)
        self.copyedit.refresh_from_db()
        self.assertFalse(self.copyedit.decision)

    def test_proofing_manager_views_reject_other_articles_task(self):
        for url_name in (
            "edit_proofing_assignment",
            "notify_proofreader",
            "request_typesetting_changes",
        ):
            with self.subTest(url_name=url_name):
                response = self.get(
                    url_name,
                    article_id=self.article.pk,
                    proofing_task_id=self.other_proofing_task.pk,
                )
                self.assertEqual(response.status_code, 404)

    def test_proofing_galley_views_reject_other_journals_task(self):
        response = self.get(
            "preview_galley",
            proofing_task_id=self.other_proofing_task.pk,
            galley_id=self.other_galley.pk,
        )
        self.assertEqual(response.status_code, 404)
        response = self.get(
            "proofing_download",
            proofing_task_id=self.other_proofing_task.pk,
            file_id=self.other_galley.file.pk,
        )
        self.assertEqual(response.status_code, 404)

    def test_review_typeset_task_rejects_other_articles_task(self):
        response = self.get(
            "review_typeset_task",
            article_id=self.article.pk,
            typeset_id=self.other_typeset_task.pk,
        )
        self.assertEqual(response.status_code, 404)
        self.other_typeset_task.refresh_from_db()
        self.assertFalse(self.other_typeset_task.editor_reviewed)

    def test_manage_proofing_assignment_rejects_other_articles_assignment(self):
        response = self.get(
            "typesetting_manage_proofing_assignment",
            article_id=self.article.pk,
            assignment_id=self.other_galley_proofing.pk,
        )
        self.assertEqual(response.status_code, 404)
