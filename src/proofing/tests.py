from django.test import TestCase
from django.shortcuts import reverse
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from proofing import models
from utils import models as utils_models
from utils import transactional_emails
from utils.testing import helpers
from submission import models as submission_models


class TestLogic(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.editor = helpers.create_user(
            "typesetter@janeway.systems",
            roles=["editor"],
            journal=cls.journal_one,
            atrrs={"is_active": True},
        )
        cls.proofreader = helpers.create_user(
            "proofreader@janeway.systems",
            roles=["proofreader"],
            journal=cls.journal_one,
        )
        cls.proofreader.is_active = True
        cls.proofreader.save()
        cls.typesetter = helpers.create_user(
            "typesetter@janeway.systems",
            roles=["typesetter"],
            journal=cls.journal_one,
        )
        cls.typesetter.is_active = True
        cls.typesetter.save()
        cls.active_article = helpers.create_article(
            journal=cls.journal_one,
        )
        cls.active_article.title = "Active Article"
        cls.active_article.save()
        cls.archived_article = helpers.create_article(
            journal=cls.journal_one,
        )
        cls.archived_article.stage = submission_models.STAGE_ARCHIVED
        cls.archived_article.title = "Archived Article"
        cls.archived_article.save()

        cls.active_proofing_assignment = models.ProofingAssignment.objects.create(
            article=cls.active_article,
            proofing_manager=cls.editor,
            editor=cls.editor,
        )
        cls.active_round = models.ProofingRound.objects.create(
            assignment=cls.active_proofing_assignment,
            number=1,
        )
        cls.active_proofing_task = models.ProofingTask.objects.create(
            round=cls.active_round,
            proofreader=cls.proofreader,
            task="Active Proofing Task",
            due=timezone.now(),
        )

        cls.archived_proofing_assignment = models.ProofingAssignment.objects.create(
            article=cls.archived_article,
            proofing_manager=cls.editor,
            editor=cls.editor,
        )
        cls.archived_round = models.ProofingRound.objects.create(
            assignment=cls.archived_proofing_assignment,
            number=1,
        )
        cls.archived_proofing_task = models.ProofingTask.objects.create(
            round=cls.archived_round,
            proofreader=cls.proofreader,
            task="Archived Proofing Task",
            due=timezone.now(),
        )

        cls.active_correction = models.TypesetterProofingTask.objects.create(
            proofing_task=cls.active_proofing_task,
            typesetter=cls.typesetter,
            task="Active Correction",
        )
        cls.archived_correction = models.TypesetterProofingTask.objects.create(
            proofing_task=cls.archived_proofing_task,
            typesetter=cls.typesetter,
            task="Active Correction",
        )

        cls.request = helpers.Request()
        cls.request.journal = cls.journal_one
        cls.request.press = cls.journal_one.press
        cls.request.site_type = cls.journal_one
        cls.request.user = cls.editor
        cls.request.model_content_type = ContentType.objects.get_for_model(
            cls.journal_one,
        )

    def test_send_proofreader_complete_notification_is_logged(self):
        transactional_emails.send_proofreader_complete_notification(
            request=self.request,
            proofing_task=self.active_proofing_task,
            article=self.active_article,
        )

        self.assertTrue(
            utils_models.LogEntry.objects.filter(
                is_email=True,
                types="Proofing Complete",
                addressee__field="to",
                addressee__email=self.editor.email,
            ).exists(),
        )

    def test_send_proofing_ack_is_logged(self):
        transactional_emails.send_proofing_ack(
            request=self.request,
            user_message="Thank you for proofing.",
            article=self.active_article,
            model_object=self.active_proofing_task,
            model_name="proofing task",
            skip=False,
        )

        self.assertTrue(
            utils_models.LogEntry.objects.filter(
                is_email=True,
                types="Proofing Acknowledgement",
                addressee__field="to",
                addressee__email=self.proofreader.email,
            ).exists(),
        )

    def test_archive_stage_hides_task(self):
        self.client.force_login(self.proofreader)
        response = self.client.get(reverse("proofing_requests"))
        self.assertContains(
            response,
            "Active Article",
        )
        self.assertNotContains(response, "Archived Article")

    def test_archived_article_task_404s(self):
        self.client.force_login(self.proofreader)
        response = self.client.get(
            reverse(
                "do_proofing", kwargs={"proofing_task_id": self.active_proofing_task.pk}
            )
        )
        self.assertTrue(
            response.status_code,
            404,
        )

    def test_active_article_task_200s(self):
        self.client.force_login(self.proofreader)
        response = self.client.get(
            reverse(
                "do_proofing",
                kwargs={"proofing_task_id": self.archived_proofing_task.pk},
            )
        )
        self.assertTrue(
            response.status_code,
            200,
        )

    def test_archive_stage_hides_correction_task(self):
        self.client.force_login(self.typesetter)
        response = self.client.get(reverse("proofing_correction_requests"))
        self.assertContains(
            response,
            f"Article ID: {self.active_article.id}",
        )
        self.assertNotContains(
            response,
            f"Article ID: {self.archived_article.id}",
        )

    def test_archived_article_correction_404s(self):
        self.client.force_login(self.typesetter)
        response = self.client.get(
            reverse(
                "typesetting_corrections",
                kwargs={"typeset_task_id": self.archived_correction.pk},
            )
        )
        self.assertTrue(
            response.status_code,
            404,
        )

    def test_active_article_correction_200s(self):
        self.client.force_login(self.typesetter)
        response = self.client.get(
            reverse(
                "typesetting_corrections",
                kwargs={"typeset_task_id": self.active_correction.pk},
            )
        )
        self.assertTrue(
            response.status_code,
            200,
        )
