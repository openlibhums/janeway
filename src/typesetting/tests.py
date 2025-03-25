__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve, Andy Byers & Mauro Sanchez"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from mock import Mock

import os

from django.test import TestCase
from django.utils import timezone
from django.http import HttpRequest
from django.core.exceptions import PermissionDenied
from django.core.files.base import ContentFile
from django.shortcuts import reverse
from django.conf import settings

from typesetting import models, security
from submission import models as submission_models
from utils import setting_handler
from utils.shared import clear_cache
from utils.testing import helpers
from core import models as core_models, urls
from core import files as core_files

from bs4 import BeautifulSoup


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

    def test_good_user_can_preview_typesetting_article(self):
        func = Mock()
        kwargs = {'assignment_id': self.typesetting_assignment.pk}
        decorated_func = security.can_preview_typesetting_article(func)

        self.typesetter.is_active = True

        request = self.prepare_request_with_user(
            self.typesetter,
            self.journal_one,
        )
        decorated_func(request, **kwargs)
        self.assertTrue(
            func.called,
        )

    def test_bad_user_cant_preview_typesetting_article(self):
        func = Mock()
        kwargs = {'assignment_id': self.typesetting_assignment.pk}
        decorated_func = security.can_preview_typesetting_article(func)

        request = self.prepare_request_with_user(
            self.article_owner,
            self.journal_one,
        )
        with self.assertRaises(PermissionDenied):
            decorated_func(request, **kwargs)

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

    def build_proofing_comparison_dict(self, published, theme):
        setting_handler.save_setting(
            'general',
            'journal_theme',
            self.journal_one,
            theme,
        )
        clear_cache()
        self.client.force_login(self.typesetter)
        if published:
            url = reverse(
                'article_view',
                kwargs={
                    'identifier_type': 'id',
                    'identifier': self.article_in_typesetting.pk,
                }
            )
        else:
            url = reverse(
                'typesetting_preview_galley',
                kwargs={
                    'article_id': self.article_in_typesetting.pk,
                    'galley_id': self.galley.pk,
                    'assignment_id': self.active_typesetting_task.pk,
                }
            )
        response = self.client.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        data = []
        include_ids = [
            'article_opener',
            'article_metadata',
            'content',  # This quite generic id in the OLH theme
                        # predates this proofing test
            'author_biographies',
        ]
        exclude_ids = [
            'article_how_to_cite',
            'article_date_published',
            'note_to_proofreader_1',
            'note_to_proofreader_2',
            'article_footer_block',
        ]
        for include_id in include_ids:
            included_element = soup.find(id=include_id)
            if not included_element:
                continue
            for exclude_id in exclude_ids:
                excluded_element = included_element.find(id=exclude_id)
                if not excluded_element:
                    continue
                excluded_element.decompose()
            data.append(included_element.prettify())
        return data

    def test_proof_matches_published_article_olh(self):
        """
        Tests whether the metadata and article text offered
        in proofing matches that of the published article.
        """

        self.maxDiff = None
        proofing = self.build_proofing_comparison_dict(False, 'OLH')
        stage_published = submission_models.STAGE_PUBLISHED
        self.article_in_typesetting.stage = stage_published
        self.article_in_typesetting.date_published = timezone.now()
        self.article_in_typesetting.save()
        published = self.build_proofing_comparison_dict(True, 'OLH')
        self.article_in_typesetting.stage = submission_models.STAGE_TYPESETTING_PLUGIN
        self.article_in_typesetting.date_published = None
        self.article_in_typesetting.save()
        self.assertEqual(proofing, published)

    def test_proof_matches_published_article_material(self):
        """
        Tests whether the metadata and article text offered
        in proofing matches that of the published article.
        """

        self.maxDiff = None
        proofing = self.build_proofing_comparison_dict(False, 'material')
        stage_published = submission_models.STAGE_PUBLISHED
        self.article_in_typesetting.stage = stage_published
        self.article_in_typesetting.date_published = timezone.now()
        self.article_in_typesetting.save()
        published = self.build_proofing_comparison_dict(True, 'material')
        self.article_in_typesetting.stage = submission_models.STAGE_TYPESETTING_PLUGIN
        self.article_in_typesetting.date_published = None
        self.article_in_typesetting.save()
        self.assertEqual(proofing, published)

    def test_proof_matches_published_article_clean(self):
        """
        Tests whether the metadata and article text offered
        in proofing matches that of the published article.
        """

        self.maxDiff = None
        proofing = self.build_proofing_comparison_dict(False, 'clean')
        stage_published = submission_models.STAGE_PUBLISHED
        self.article_in_typesetting.stage = stage_published
        self.article_in_typesetting.date_published = timezone.now()
        self.article_in_typesetting.save()
        published = self.build_proofing_comparison_dict(True, 'clean')
        self.article_in_typesetting.stage = submission_models.STAGE_TYPESETTING_PLUGIN
        self.article_in_typesetting.date_published = None
        self.article_in_typesetting.save()
        self.assertEqual(proofing, published)

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
            **{'first_name': 'Kat', 'last_name': 'Janeway', 'is_active': True}
        )

        self.typesetter.is_active = True
        self.typesetter.save()


        self.article_in_typesetting = submission_models.Article.objects.create(
            owner=self.article_owner,
            title="A Test Article",
            abstract="An abstract",
            stage=submission_models.STAGE_TYPESETTING_PLUGIN,
            journal_id=self.journal_one.id,
            first_page=28,
            last_page=64,
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
            element_name='Typesetting',
            handshake_url='dummy',
            jump_url='dummy',
            stage=submission_models.STAGE_TYPESETTING_PLUGIN,
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

        self.test_file_name = 'test_galley.xml'
        self.test_file_path = os.path.join(
            settings.BASE_DIR,
            'typesetting',
            self.test_file_name,
        )

        with open(self.test_file_path, 'rb') as test_file:
            content_file = ContentFile(test_file.read())
            content_file.name = self.test_file_name
            self.galley_file = core_files.save_file_to_article(
                content_file,
                self.article_in_typesetting,
                self.typesetter
            )

        self.galley, created = core_models.Galley.objects.get_or_create(
            article=self.article_in_typesetting,
            label='XML',
            type='xml',
            defaults={'file': self.galley_file},
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

    @classmethod
    def tearDownClass(cls):
        cls.galley.unlink_files()
