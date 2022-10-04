__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve, Andy Byers & Mauro Sanchez"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from mock import Mock

from django.test import TestCase
from django.utils import timezone
from django.http import HttpRequest
from django.core.exceptions import PermissionDenied
from django.shortcuts import reverse

from plugins.typesetting import plugin_settings, models, security
from submission import models as submission_models
from utils.testing import helpers
from core import models as core_models, urls


class TestTypesetting(TestCase):

    @staticmethod
    def mock_messages_add(level, message, extra_tags):
        pass

    @staticmethod
    def get_method(field):
        return None

    @staticmethod
    def prepare_request_with_user(user, journal, press=None):
        """
        Build a basic request dummy object with the journal set to journal
        and the user having editor permissions.
        :param user: the user to use
        :param journal: the journal to use
        :return: an object with user and journal properties
        """
        request = Mock(HttpRequest)
        request.user = user
        request.GET = Mock()
        request.GET.get = TestTypesetting.get_method
        request.journal = journal
        request._messages = Mock()
        request._messages.add = TestTypesetting.mock_messages_add
        request.path = '/a/fake/path/'
        request.path_info = '/a/fake/path/'
        request.press = press

        return request

    def test_proofreader_for_article_required(self):
        """
        Tests that an assigned user can pas this check
        """
        func = Mock()
        kwargs = {'assignment_id': self.galley_proofing.pk}
        decorated_func = security.proofreader_for_article_required(func)
        request = self.prepare_request_with_user(
            self.proofreader,
            self.journal_one,
        )

        decorated_func(request, **kwargs)

        self.assertTrue(
            func.called, 
            "Security Error: Proofreader cannot access proofing task.",
        )

    def test_proofreader_for_article_required_bad_user(self):
        """
        Tests a bad user cannot pass this check
        """
        func = Mock()
        kwargs = {'assignment_id': self.galley_proofing.pk}
        decorated_func = security.proofreader_for_article_required(func)
        request = self.prepare_request_with_user(
            self.article_owner,
            self.journal_one,
        )

        with self.assertRaises(PermissionDenied):
            # test that editor_user_required raises a PermissionDenied exception
            decorated_func(request, **kwargs)

        self.assertFalse(
            func.called,
            "Security Error: Priviledged user able to access prooding task."
        ) 


    def test_require_not_notified(self):
        """
        Tests that an assigned user can pas this check
        """
        func = Mock()
        kwargs = {'assignment_id': self.galley_proofing.pk}
        decorator = security.require_not_notified(models.GalleyProofing)
        request = self.prepare_request_with_user(
            self.editor,
            self.journal_one,
        )

        decorated_func = decorator(func)
        decorated_func(request, **kwargs)

        self.assertTrue(
            func.called, 
            "Security Error: Editor can't bypass require_not_notified.",
        )

    def test_require_not_notified_with_notifed_true(self):
        """
        Tests that an assigned user can pas this check
        """
        func = Mock()
        kwargs = {'assignment_id': self.galley_proofing_notified.pk}
        decorator = security.require_not_notified(models.GalleyProofing)
        request = self.prepare_request_with_user(
            self.editor,
            self.journal_one,
        )

        decorated_func = decorator(func)

        with self.assertRaises(PermissionDenied):
            decorated_func(request, **kwargs)

        self.assertFalse(
            func.called, 
            "Security Error: Editor can bypass require_not_notified.",
        )

    def test_can_manage_file(self):
        func = Mock()
        kwargs = {'file_id': self.private_file.pk}
        decorated_func = security.user_can_manage_file(func)

        users = [self.production_manager, self.editor]

        for user in users:
            request = self.prepare_request_with_user(
                self.production_manager,
                self.journal_one,
            )
            
            decorated_func(request, **kwargs)

            self.assertTrue(
                func.called,
                "Security Error: Priviledged user cannot manage file."
            ) 

    def test_can_manage_file_bad_user(self):
        func = Mock()
        kwargs = {'file_id': self.private_file.pk}
        decorated_func = security.user_can_manage_file(func)

        users = [self.typesetter, self.bad_user, self.proofreader]

        for user in users:
            request = self.prepare_request_with_user(
                self.typesetter,
                self.journal_one,
            )
            
            with self.assertRaises(PermissionDenied):
                # test that editor_user_required raises a PermissionDenied 
                # exception
                decorated_func(request, **kwargs)

            self.assertFalse(
                func.called,
                "Security Error: Non priviledged user can manage file."
            )

    def test_archive_stage_hides_task(self):
        self.client.force_login(self.typesetter)
        response = self.client.get(
            reverse('typesetting_assignments')
        )
        self.assertContains(
            response,
            'Active Article',
        )
        self.assertNotContains(
            response,
            'Archived Article'
        )

    def test_archived_article_task_404s(self):
        self.client.force_login(self.typesetter)
        response = self.client.get(
            reverse(
                'typesetting_assignment',
                kwargs={
                    'assignment_id': self.archived_typesetting_task.pk
                }
            )
        )
        self.assertTrue(
            response.status_code,
            404,
        )

    def test_active_article_task_200s(self):
        self.client.force_login(self.typesetter)
        response = self.client.get(
            reverse(
                'typesetting_assignment',
                kwargs={
                    'assignment_id': self.active_typesetting_task.pk
                }
            )
        )
        self.assertTrue(
            response.status_code,
            200,
        )

    @classmethod
    def setUpTestData(self):
        """
        Setup the test environment.
        :return: None
        """
        roles_to_setup = [
            "reviewer",
            "editor",
            "production",
            "typesetter",
            "proofreader",
        ]
        helpers.create_press()
        self.journal_one, self.journal_two = helpers.create_journals()
        helpers.create_roles(roles_to_setup)

        self.editor = helpers.create_editor(self.journal_one)
        self.article_owner = helpers.create_regular_user()
        self.bad_user = helpers.create_second_user(self.journal_one)
        self.proofreader = helpers.create_user(
            username='proofer@janeway.systems',
            roles=['proofreader'],
            journal=self.journal_one,
        )

        self.proofreader.is_active = True
        self.proofreader.save()

        self.production_manager = helpers.create_user(
            username='production_manager@janeway.systems',
            roles=['production'],
            journal=self.journal_one,
        )
        self.typesetter = helpers.create_user(
            username='typesetter@janeway.systems',
            roles=['typesetter'],
            journal=self.journal_one,
        )
        self.typesetter.is_active = True
        self.typesetter.save()

        self.article_in_typesetting = submission_models.Article.objects.create(
            owner=self.article_owner,
            title="A Test Article",
            abstract="An abstract",
            stage=plugin_settings.STAGE,
            journal_id=self.journal_one.id
        )

        self.private_file = core_models.File.objects.create(
            mime_type="A/FILE",
            original_filename="blah.txt",
            uuid_filename="UUID.txt",
            label="A file that is private",
            description="Oh yes, it's a file",
            owner=self.article_owner,
            is_galley=False,
            privacy="owner",
            article_id=self.article_in_typesetting.pk
        )

        self.workflow_element = core_models.WorkflowElement.objects.create(
            journal=self.journal_one,
            element_name='Typesetting Plugin',
            handshake_url='dummy',
            jump_url='dummy',
            stage=plugin_settings.STAGE,
            article_url=True,
        )

        self.workflow_log_entry = core_models.WorkflowLog.objects.create(
            article=self.article_in_typesetting,
            element=self.workflow_element,
        )

        self.typesetting_round = models.TypesettingRound.objects.create(
            article=self.article_in_typesetting,
        )

        self.typesetting_assignment = models.TypesettingAssignment.objects.create(
            round=self.typesetting_round,
            manager=self.editor,
            typesetter=self.typesetter,
            due=timezone.now(),
        )

        self.galley_proofing = models.GalleyProofing.objects.create(
            round=self.typesetting_round,
            manager=self.editor,
            proofreader=self.proofreader,
            due=timezone.now(),
        )

        self.galley_proofing_notified = models.GalleyProofing.objects.create(
            round=self.typesetting_round,
            manager=self.editor,
            proofreader=self.proofreader,
            due=timezone.now(),
            notified=True,
        )

        self.author = helpers.create_user(
            'author@janeway.systems',
            ['author'],
            journal=self.journal_one,
        )
        self.author.is_active = True
        self.author.save()
        self.active_article = helpers.create_article(
            journal=self.journal_one,
        )
        self.active_article.title = 'Active Article'
        self.active_article.save()
        self.active_article.authors.add(self.author)
        self.archived_article = helpers.create_article(
            journal=self.journal_one,
        )
        self.archived_article.stage = submission_models.STAGE_ARCHIVED
        self.archived_article.title = 'Archived Article'
        self.archived_article.save()
        self.archived_article.authors.add(self.author)

        self.active_typesetting_round = models.TypesettingRound.objects.create(
            article=self.active_article,
        )
        self.active_typesetting_task = models.TypesettingAssignment.objects.create(
            round=self.active_typesetting_round,
            manager=self.editor,
            typesetter=self.typesetter,
            task='Active Task',
        )

        self.archived_typesetting_round = models.TypesettingRound.objects.create(
            article=self.archived_article,
        )
        self.archived_typesetting_task = models.TypesettingAssignment.objects.create(
            round=self.archived_typesetting_round,
            manager=self.editor,
            typesetter=self.typesetter,
            task='Archived Task',
        )
