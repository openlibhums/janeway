__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


import datetime

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpRequest, HttpResponseRedirect
from django.test import TestCase
from django.utils import timezone
from django.test.utils import override_settings
from django.urls import reverse
from django.core.management import call_command
from mock import Mock

from core import models as core_models, forms as core_forms
from journal import models as journal_models
from production import models as production_models
from security import decorators
from review import models as review_models
from submission import models as submission_models
from copyediting import models as copyediting_models
from proofing import models as proofing_models
from repository import models as repository_models
from press import models as press_models
from utils.install import update_xsl_files, update_settings
from utils import setting_handler
from utils.testing import helpers


class TestSecurity(TestCase):
    # Tests for editor role checks

    def test_account_is_editor_role_check_blocks_non_editors(self):
        """
        Tests that the internal Account.is_editor function blocks non-editors.
        :return: None or raises an assertion
        """
        request = self.prepare_request_with_user(self.regular_user, self.journal_one)

        # test the internal user role handling for non-editors
        self.assertFalse(self.regular_user.is_editor(request),
                         "Account.is_editor wrongly allows non-editors to access editor content")

    def test_account_role_check_blocks_non_editors(self):
        """
        Tests that the Account.check_role function blocks non-editors
        :return: None or raises an assertion
        """

        # test the internal user role handling for non-editors
        self.assertFalse(self.regular_user.check_role(self.journal_one, "editor"),
                         "Account.check_role wrongly allows non-editors to access editor content")

    def test_account_is_editor_role_check_allows_editors(self):
        """
        Tests that the internal Account.is_editor function allows editors.
        :return: None or raises an assertion
        """
        request = self.prepare_request_with_user(self.editor, self.journal_one)

        # test the internal user role handling for non-editors
        self.assertTrue(self.editor.is_editor(request),
                        "Account.is_editor wrongly blocks editors from accessing editor content")

    def test_account_role_check_allows_editors(self):
        """
        Tests that the internal Account.check_role function allows editors.
        :return: None or raises an assertion
        """

        # test the internal user role handling for non-editors
        self.assertTrue(self.editor.check_role(self.journal_one, "editor"),
                        "Account.check_role wrongly blocks editors from accessing editor content")

    def test_reviewer_user_required_decorator_handles_null_user(self):
        """
        Tests that the reviewer_user_required decorator can handle a null request object.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.reviewer_user_required(func)

        request = self.prepare_request_with_user(None, self.journal_one)

        self.assertIsInstance(decorated_func(request), HttpResponseRedirect)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "reviewer_user_required decorator incorrectly handles request.user=None")

    def test_reviewer_user_required_decorator_blocks_anonymous_users(self):
        """
        Tests that the internal Account.is_editor function blocks anonymous users.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.reviewer_user_required(func)

        anon_user = AnonymousUser()
        request = self.prepare_request_with_user(anon_user, self.journal_one)

        self.assertIsInstance(decorated_func(request), HttpResponseRedirect)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "reviewer_user_required decorator wrongly allows anonymous users to access editor content")

    def test_reviewer_user_required_decorator_blocks_non_reviewers(self):
        """
        Tests that the reviewer_user_required decorator blocks non-reviewers.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.reviewer_user_required(func)

        # first test is with a non-editor
        request = self.prepare_request_with_user(self.regular_user, self.journal_one)

        with self.assertRaises(PermissionDenied):
            # test that reviewer_user_required raises a PermissionDenied exception
            decorated_func(request)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "reviewer_user_required decorator wrongly allows non-editors to access editor content")

    def test_reviewer_user_required_decorator_allows_editors(self):
        """
        Tests that the reviewer_user_required decorator allows reviewers.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.reviewer_user_required(func)

        # second test set is with an editor and should perform in the opposite way to the block
        request = self.prepare_request_with_user(self.second_user, self.journal_one)

        # call this function which should not throw an error this time
        decorated_func(request)

        # test that the callback was called
        self.assertTrue(func.called, "reviewer_user_required decorator wrongly prohibits editors from accessing "
                                     "content")

    def test_reviewer_user_required_decorator_allows_staff(self):
        """
        Tests that the reviewer_user_required decorator allows staff.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.reviewer_user_required(func)

        request = self.prepare_request_with_user(self.admin_user, self.journal_one)

        # call this function which should not throw an error this time
        decorated_func(request)

        # test that the callback was called
        self.assertTrue(func.called, "reviewer_user_required decorator wrongly prohibits staff from accessing content")

    def test_reviewer_user_required_decorator_isolates_journals(self):
        """
        Tests that the reviewer_user_required decorator does not allow an editor on one journal to review on a different
        journal.
        :return: None or raises an assertion
        """

        # now test that a user with editor permissions on journal one cannot access editorial on journal two
        func = Mock()
        decorated_func = decorators.reviewer_user_required(func)

        request = self.prepare_request_with_user(self.second_user, self.journal_two)

        with self.assertRaises(PermissionDenied):
            # test that reviewer_user_required raises a PermissionDenied exception
            decorated_func(request)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "reviewer_user_required decorator wrongly allows editors to access editor content on other "
                         "journals")

    def test_reviewer_user_required_decorator_blocks_authors(self):
        """
        Tests that the reviewer_user_required decorator does not allow an author to view reviewer pages.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.reviewer_user_required(func)

        request = self.prepare_request_with_user(self.author, self.journal_one)

        with self.assertRaises(PermissionDenied):
            # test that reviewer_user_required raises a PermissionDenied exception
            decorated_func(request)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "reviewer_user_required decorator wrongly allows authors to access editor content")

    def test_reviewer_user_required_decorator_blocks_proofreaders(self):
        """
        Tests that the reviewer_user_required decorator does not allow an author to view reviewer pages.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.reviewer_user_required(func)

        request = self.prepare_request_with_user(self.proofreader, self.journal_one)

        with self.assertRaises(PermissionDenied):
            # test that reviewer_user_required raises a PermissionDenied exception
            decorated_func(request)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "reviewer_user_required decorator wrongly allows proofreaders to access editor content")

    def test_reviewer_user_required_decorator_blocks_inactive_users(self):
        """
        Tests that the reviewer_user_required decorator does not allow an inactive to view reviewer pages.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.reviewer_user_required(func)

        request = self.prepare_request_with_user(self.inactive_user, self.journal_one)

        self.assertIsInstance(decorated_func(request), HttpResponseRedirect)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "reviewer_user_required decorator wrongly allows inactive users to access author content")

    def test_editor_user_required_decorator_handles_null_user(self):
        """
        Tests that the editor_user_required decorator can handle a null request object.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.editor_user_required(func)

        request = self.prepare_request_with_user(None, self.journal_one)

        self.assertIsInstance(decorated_func(request), HttpResponseRedirect)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "editor_user_required decorator incorrectly handles request.user=None")

    def test_editor_user_required_decorator_blocks_anonymous_users(self):
        """
        Tests that the internal Account.is_editor function blocks anonymous users.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.editor_user_required(func)

        anon_user = AnonymousUser()
        request = self.prepare_request_with_user(anon_user, self.journal_one)

        self.assertIsInstance(decorated_func(request), HttpResponseRedirect)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "editor_user_required decorator wrongly allows anonymous users to access editor content")

    def test_editor_user_required_decorator_blocks_non_editors(self):
        """
        Tests that the editor_user_required decorator blocks non-editors.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.editor_user_required(func)

        # first test is with a non-editor
        request = self.prepare_request_with_user(self.regular_user, self.journal_one)

        with self.assertRaises(PermissionDenied):
            # test that editor_user_required raises a PermissionDenied exception
            decorated_func(request)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "editor_user_required decorator wrongly allows non-editors to access editor content")

    def test_editor_user_required_decorator_allows_editors(self):
        """
        Tests that the editor_user_required decorator allows editors.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.editor_user_required(func)

        # second test set is with an editor and should perform in the opposite way to the block
        request = self.prepare_request_with_user(self.editor, self.journal_one)

        # call this function which should not throw an error this time
        decorated_func(request)

        # test that the callback was called
        self.assertTrue(func.called, "editor_user_required decorator wrongly prohibits editors from accessing content")

    def test_editor_user_required_decorator_allows_staff(self):
        """
        Tests that the editor_user_required decorator allows staff.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.editor_user_required(func)

        request = self.prepare_request_with_user(self.admin_user, self.journal_one)

        # call this function which should not throw an error this time
        decorated_func(request)

        # test that the callback was called
        self.assertTrue(func.called, "editor_user_required decorator wrongly prohibits staff from accessing content")

    def test_editor_user_required_decorator_isolates_journals(self):
        """
        Tests that the editor_user_required decorator does not allow an editor on one journal to edit a different
        journal.
        :return: None or raises an assertion
        """

        # now test that a user with editor permissions on journal one cannot access editorial on journal two
        func = Mock()
        decorated_func = decorators.editor_user_required(func)

        request = self.prepare_request_with_user(self.editor, self.journal_two)

        with self.assertRaises(PermissionDenied):
            # test that editor_user_required raises a PermissionDenied exception
            decorated_func(request)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "editor_user_required decorator wrongly allows editors to access editor content on other "
                         "journals")

    def test_editor_user_required_decorator_blocks_authors(self):
        """
        Tests that the editor_user_required decorator does not allow an author to view editor pages.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.editor_user_required(func)

        request = self.prepare_request_with_user(self.author, self.journal_one)

        with self.assertRaises(PermissionDenied):
            # test that editor_user_required raises a PermissionDenied exception
            decorated_func(request)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "editor_user_required decorator wrongly allows authors to access editor content")

    def test_editor_user_required_decorator_blocks_proofreaders(self):
        """
        Tests that the editor_user_required decorator does not allow an author to view editor pages.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.editor_user_required(func)

        request = self.prepare_request_with_user(self.proofreader, self.journal_one)

        with self.assertRaises(PermissionDenied):
            # test that editor_user_required raises a PermissionDenied exception
            decorated_func(request)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "editor_user_required decorator wrongly allows proofreaders to access editor content")

    def test_editor_user_required_decorator_blocks_inactive_users(self):
        """
        Tests that the editor_user_required decorator does not allow an inactive to view editor pages.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.editor_user_required(func)

        request = self.prepare_request_with_user(self.inactive_user, self.journal_one)

        self.assertIsInstance(decorated_func(request), HttpResponseRedirect)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "editor_user_required decorator wrongly allows inactive users to access author content")

    # Tests for author role checks
    def test_account_is_author_role_check_blocks_non_authors(self):
        """
        Tests that the internal Account.is_author function blocks non-authors.
        :return: None or raises an assertion
        """
        request = self.prepare_request_with_user(self.regular_user, self.journal_one)

        # test the internal user role handling for non-editors
        self.assertFalse(self.regular_user.is_editor(request),
                         "Account.is_author wrongly allows non-authors to access author content")

    def test_account_role_check_blocks_non_authors(self):
        """
        Tests that the Account.check_role function blocks non-authors.
        :return: None or raises an assertion
        """

        # test the internal user role handling for non-editors
        self.assertFalse(self.regular_user.check_role(self.journal_one, "author"),
                         "Account.check_role wrongly allows non-authors to access author content")

    def test_account_is_author_role_check_allows_authors(self):
        """
        Tests that the internal Account.is_editor function allows editors.
        :return: None or raises an assertion
        """
        request = self.prepare_request_with_user(self.editor, self.journal_one)

        # test the internal user role handling for non-editors
        self.assertTrue(self.author.is_author(request),
                        "Account.is_editor wrongly blocks authors from accessing author content")

    def test_account_role_check_allows_authors(self):
        """
        Tests that the internal Account.check_role function allows authors.
        :return: None or raises an assertion
        """

        # test the internal user role handling for non-editors
        self.assertTrue(self.author.check_role(self.journal_one, "author"),
                        "Account.check_role wrongly blocks authors from accessing author content")

    def test_author_user_required_decorator_blocks_anonymous_users(self):
        """
        Tests that the author_user_required decorator blocks anonymous users.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.author_user_required(func)

        anon_user = AnonymousUser()
        request = self.prepare_request_with_user(anon_user, self.journal_one)

        self.assertIsInstance(decorated_func(request), HttpResponseRedirect)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "author_user_required decorator wrongly allows anonymous users to access author content")

    def test_author_user_required_decorator_handles_null_user(self):
        """
        Tests that the author_user_required decorator can handle a null request object.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.author_user_required(func)

        request = self.prepare_request_with_user(None, self.journal_one)

        self.assertIsInstance(decorated_func(request), HttpResponseRedirect)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "author_user_required decorator incorrectly handles request.user=None")

    def test_author_user_required_decorator_blocks_non_authors(self):
        """
        Tests that the author_user_required decorator blocks non-authors.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.author_user_required(func)

        # first test is with a non-editor
        request = self.prepare_request_with_user(self.regular_user, self.journal_one)

        with self.assertRaises(PermissionDenied):
            # test that editor_user_required raises a PermissionDenied exception
            decorated_func(request)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "author_user_required decorator wrongly allows non-authors to access author content")

    def test_author_user_required_decorator_allows_authors(self):
        """
        Tests that the author_user_required decorator allows authors.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.author_user_required(func)

        # second test set is with an editor and should perform in the opposite way to the block
        request = self.prepare_request_with_user(self.author, self.journal_one)

        # call this function which should not throw an error this time
        decorated_func(request)

        # test that the callback was called
        self.assertTrue(func.called, "author_user_required decorator wrongly prohibits authors from accessing content")

    def test_author_user_required_decorator_allows_staff(self):
        """
        Tests that the author_user_required decorator allows staff.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.author_user_required(func)

        request = self.prepare_request_with_user(self.admin_user, self.journal_one)

        # call this function which should not throw an error this time
        decorated_func(request)

        # test that the callback was called
        self.assertTrue(func.called, "author_user_required decorator wrongly prohibits staff from accessing content")

    def test_author_user_required_decorator_isolates_journals(self):
        """
        Tests that the author_user_required decorator does not allow an author on one journal to see author content on
        a different journal.
        :return: None or raises an assertion
        """

        # now test that a user with editor permissions on journal one cannot access editorial on journal two
        func = Mock()
        decorated_func = decorators.editor_user_required(func)

        request = self.prepare_request_with_user(self.author, self.journal_two)

        with self.assertRaises(PermissionDenied):
            # test that editor_user_required raises a PermissionDenied exception
            decorated_func(request)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "author_user_required decorator wrongly allows authors to access editor content on other "
                         "journals")

    def test_author_user_required_decorator_blocks_editors(self):
        """
        Tests that the author_user_required decorator does not allow an editor to view author pages.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.author_user_required(func)

        request = self.prepare_request_with_user(self.editor, self.journal_one)

        with self.assertRaises(PermissionDenied):
            # test that editor_user_required raises a PermissionDenied exception
            decorated_func(request)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "author_user_required decorator wrongly allows editors to access author content")

    def test_author_user_required_decorator_blocks_proofreaders(self):
        """
        Tests that the author_user_required decorator does not allow an editor to view author pages.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.author_user_required(func)

        request = self.prepare_request_with_user(self.proofreader, self.journal_one)

        with self.assertRaises(PermissionDenied):
            # test that editor_user_required raises a PermissionDenied exception
            decorated_func(request)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "author_user_required decorator wrongly allows proofreaders to access author content")

    def test_author_user_required_decorator_blocks_inactive_users(self):
        """
        Tests that the author_user_required decorator does not allow an inactive to view author pages.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.author_user_required(func)

        request = self.prepare_request_with_user(self.inactive_user, self.journal_one)

        self.assertIsInstance(decorated_func(request), HttpResponseRedirect)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "author_user_required decorator wrongly allows inactive users to access author content")

    # Tests for proofreader role checks
    def test_account_is_proofreader_role_check_blocks_non_proofreaders(self):
        """
        Tests that the internal Account.is_proofreader function blocks non-proofreaders.
        :return: None or raises an assertion
        """
        request = self.prepare_request_with_user(self.regular_user, self.journal_one)

        # test the internal user role handling for non-editors
        self.assertFalse(self.regular_user.is_editor(request),
                         "Account.is_proofreader wrongly allows non-proofreaders to access proofreader content")

    def test_account_role_check_blocks_non_proofreaders(self):
        """
        Tests that the Account.check_role function blocks non-proofreaders.
        :return: None or raises an assertion
        """

        # test the internal user role handling for non-editors
        self.assertFalse(self.regular_user.check_role(self.journal_one, "proofreader"),
                         "Account.check_role wrongly allows non-proofreaders to access proofreader content")

    def test_account_is_proofreader_role_check_allows_proofreaders(self):
        """
        Tests that the internal Account.is_editor function allows editors.
        :return: None or raises an assertion
        """
        request = self.prepare_request_with_user(self.editor, self.journal_one)

        # test the internal user role handling for non-editors
        self.assertTrue(self.proofreader.is_proofreader(request),
                        "Account.is_editor wrongly blocks proofreaders from accessing proofreader content")

    def test_account_role_check_allows_proofreaders(self):
        """
        Tests that the internal Account.check_role function allows proofreaders.
        :return: None or raises an assertion
        """

        # test the internal user role handling for non-editors
        self.assertTrue(self.proofreader.check_role(self.journal_one, "proofreader"),
                        "Account.check_role wrongly blocks proofreaders from accessing proofreader content")

    def test_proofreader_user_required_decorator_blocks_anonymous_users(self):
        """
        Tests that the proofreader_user_required decorator blocks anonymous users.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.proofreader_user_required(func)

        anon_user = AnonymousUser()
        request = self.prepare_request_with_user(anon_user, self.journal_one)

        self.assertIsInstance(decorated_func(request), HttpResponseRedirect)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "proofreader_user_required decorator wrongly allows anonymous users to access proofreader "
                         "content")

    def test_proofreader_user_required_decorator_handles_null_user(self):
        """
        Tests that the author_user_required decorator can handle a null request object.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.proofreader_user_required(func)

        request = self.prepare_request_with_user(None, self.journal_one)

        self.assertIsInstance(decorated_func(request), HttpResponseRedirect)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "proofreader_user_required decorator incorrectly handles request.user=None")

    def test_proofreader_user_required_decorator_blocks_non_proofreaders(self):
        """
        Tests that the proofreader_user_required decorator blocks non-proofreaders.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.proofreader_user_required(func)

        # first test is with a non-editor
        request = self.prepare_request_with_user(self.regular_user, self.journal_one)

        with self.assertRaises(PermissionDenied):
            # test that editor_user_required raises a PermissionDenied exception
            decorated_func(request)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "proofreader_user_required decorator wrongly allows non-proofreaders to access proofreader "
                         "content")

    def test_proofreader_user_required_decorator_allows_proofreaders(self):
        """
        Tests that the proofreader_user_required decorator allows proofreaders.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.proofreader_user_required(func)

        # second test set is with an editor and should perform in the opposite way to the block
        request = self.prepare_request_with_user(self.proofreader, self.journal_one)

        # call this function which should not throw an error this time
        decorated_func(request)

        # test that the callback was called
        self.assertTrue(func.called,
                        "proofreader_user_required decorator wrongly prohibits proofreaders from accessing content")

    def test_proofreader_user_required_decorator_allows_staff(self):
        """
        Tests that the proofreader_user_required decorator allows staff.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.proofreader_user_required(func)

        request = self.prepare_request_with_user(self.admin_user, self.journal_one)

        # call this function which should not throw an error this time
        decorated_func(request)

        # test that the callback was called
        self.assertTrue(func.called,
                        "proofreader_user_required decorator wrongly prohibits staff from accessing content")

    def test_proofreader_user_required_decorator_isolates_journals(self):
        """
        Tests that the proofreader_user_required decorator does not allow an proofreader on one journal to see
        proofreader content on a different journal.
        :return: None or raises an assertion
        """

        func = Mock()
        decorated_func = decorators.editor_user_required(func)

        request = self.prepare_request_with_user(self.proofreader, self.journal_two)

        with self.assertRaises(PermissionDenied):
            # test that editor_user_required raises a PermissionDenied exception
            decorated_func(request)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "proofreader_user_required decorator wrongly allows proofreaders to access editor content on "
                         "other journals")

    def test_proofreader_user_required_decorator_blocks_editors(self):
        """
        Tests that the proofreader_user_required decorator does not allow an editor to view proofreader pages.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.proofreader_user_required(func)

        request = self.prepare_request_with_user(self.editor, self.journal_one)

        with self.assertRaises(PermissionDenied):
            # test that editor_user_required raises a PermissionDenied exception
            decorated_func(request)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "proofreader_user_required decorator wrongly allows editors to access proofreader content")

    def test_proofreader_user_required_decorator_blocks_authors(self):
        """
        Tests that the proofreader_user_required decorator does not allow production to view proofreader pages.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.proofreader_user_required(func)

        request = self.prepare_request_with_user(self.author, self.journal_one)

        with self.assertRaises(PermissionDenied):
            decorated_func(request)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "proofreader_user_required decorator wrongly allows authors to access proofreader content")

    def test_proofreader_user_required_decorator_blocks_productions(self):
        """
        Tests that the proofreader_user_required decorator does not allow production to view production pages.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.proofreader_user_required(func)

        request = self.prepare_request_with_user(self.production, self.journal_one)

        with self.assertRaises(PermissionDenied):
            decorated_func(request)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "proofreader_user_required decorator wrongly allows authors to access proofreader content")

    def test_proofreader_user_required_decorator_blocks_inactive_users(self):
        """
        Tests that the proofreader_user_required decorator does not allow an inactive to view proofreader pages.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.proofreader_user_required(func)

        request = self.prepare_request_with_user(self.inactive_user, self.journal_one)

        self.assertIsInstance(decorated_func(request), HttpResponseRedirect)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "proofreader_user_required decorator wrongly allows inactive users to access proofreader "
                         "content")

    # Tests for production role checks
    def test_account_is_production_role_check_blocks_non_productions(self):
        """
        Tests that the internal Account.is_production function blocks non-productions.
        :return: None or raises an assertion
        """
        request = self.prepare_request_with_user(self.regular_user, self.journal_one)

        # test the internal user role handling for non-editors
        self.assertFalse(self.regular_user.is_editor(request),
                         "Account.is_production wrongly allows non-productions to access production content")

    def test_account_role_check_blocks_non_productions(self):
        """
        Tests that the Account.check_role function blocks non-productions.
        :return: None or raises an assertion
        """

        # test the internal user role handling for non-editors
        self.assertFalse(self.regular_user.check_role(self.journal_one, "production"),
                         "Account.check_role wrongly allows non-productions to access production content")

    def test_account_is_production_role_check_allows_productions(self):
        """
        Tests that the internal Account.is_editor function allows editors.
        :return: None or raises an assertion
        """
        request = self.prepare_request_with_user(self.editor, self.journal_one)

        # test the internal user role handling for non-editors
        self.assertTrue(self.production.is_production(request),
                        "Account.is_editor wrongly blocks productions from accessing production content")

    def test_account_role_check_allows_productions(self):
        """
        Tests that the internal Account.check_role function allows productions.
        :return: None or raises an assertion
        """

        # test the internal user role handling for non-editors
        self.assertTrue(self.production.check_role(self.journal_one, "production"),
                        "Account.check_role wrongly blocks productions from accessing production content")

    def test_production_user_or_editor_required_decorator_blocks_anonymous_users(self):
        """
        Tests that the production_user_or_editor_required decorator blocks anonymous users.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.production_user_or_editor_required(func)

        anon_user = AnonymousUser()
        request = self.prepare_request_with_user(anon_user, self.journal_one)

        self.assertIsInstance(decorated_func(request), HttpResponseRedirect)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "production_user_or_editor_required decorator wrongly allows anonymous users to access "
                         "production content")

    def test_production_user_or_editor_required_decorator_blocks_non_productions(self):
        """
        Tests that the production_user_or_editor_required decorator blocks non-productions.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.production_user_or_editor_required(func)

        # first test is with a non-editor
        request = self.prepare_request_with_user(self.regular_user, self.journal_one)

        with self.assertRaises(PermissionDenied):
            # test that editor_user_required raises a PermissionDenied exception
            decorated_func(request)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "production_user_or_editor_required decorator wrongly allows non-productions to access "
                         "production content")

    def test_production_user_or_editor_required_decorator_handles_null_user(self):
        """
        Tests that the author_user_required decorator can handle a null request object.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.production_user_or_editor_required(func)

        request = self.prepare_request_with_user(None, self.journal_one)

        self.assertIsInstance(decorated_func(request), HttpResponseRedirect)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "production_user_or_editor_required decorator incorrectly handles request.user=None")

    def test_production_user_or_editor_required_decorator_allows_productions(self):
        """
        Tests that the production_user_or_editor_required decorator allows productions.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.production_user_or_editor_required(func)

        # second test set is with an editor and should perform in the opposite way to the block
        request = self.prepare_request_with_user(self.production, self.journal_one)

        # call this function which should not throw an error this time
        decorated_func(request)

        # test that the callback was called
        self.assertTrue(func.called,
                        "production_user_or_editor_required decorator wrongly prohibits productions from accessing "
                        "content")

    def test_production_user_or_editor_required_decorator_allows_staff(self):
        """
        Tests that the production_user_or_editor_required decorator allows staff.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.production_user_or_editor_required(func)

        request = self.prepare_request_with_user(self.admin_user, self.journal_one)

        # call this function which should not throw an error this time
        decorated_func(request)

        # test that the callback was called
        self.assertTrue(func.called,
                        "production_user_or_editor_required decorator wrongly prohibits staff from accessing content")

    def test_production_user_or_editor_required_decorator_isolates_journals(self):
        """
        Tests that the production_user_or_editor_required decorator does not allow an production on one journal to see
        production content on a different journal.
        :return: None or raises an assertion
        """

        func = Mock()
        decorated_func = decorators.editor_user_required(func)

        request = self.prepare_request_with_user(self.production, self.journal_two)

        with self.assertRaises(PermissionDenied):
            # test that editor_user_required raises a PermissionDenied exception
            decorated_func(request)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "production_user_or_editor_required decorator wrongly allows productions to access editor "
                         "content on other journals")

    def test_production_user_or_editor_required_decorator_allows_editors(self):
        """
        Tests that the production_user_or_editor_required decorator *does* allow an editor to view production pages.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.production_user_or_editor_required(func)

        request = self.prepare_request_with_user(self.editor, self.journal_one)

        decorated_func(request)

        # test that the callback was called
        self.assertTrue(func.called,
                        "production_user_or_editor_required decorator wrongly allows editors to access production "
                        "content")

    def test_production_user_or_editor_required_decorator_blocks_authors(self):
        """
        Tests that the production_user_or_editor_required decorator does not allow an author to view production pages.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.production_user_or_editor_required(func)

        request = self.prepare_request_with_user(self.author, self.journal_one)

        with self.assertRaises(PermissionDenied):
            decorated_func(request)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "production_user_or_editor_required decorator wrongly allows authors to access production "
                         "content")

    def test_production_user_or_editor_required_decorator_blocks_inactive_users(self):
        """
        Tests that the production_user_or_editor_required decorator does not allow an inactive to view production pages.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.production_user_or_editor_required(func)

        request = self.prepare_request_with_user(self.inactive_user, self.journal_one)

        self.assertIsInstance(decorated_func(request), HttpResponseRedirect)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "production_user_or_editor_required decorator wrongly allows inactive users to access "
                         "production content")

    # Tests for article_production_user_required
    def test_article_production_user_required_allows_production(self):
        """
        Tests that article_production_user_required allows the correct production user to view the article.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_production_user_required(func)

        request = self.prepare_request_with_user(self.production, self.journal_one)
        kwargs = {'article_id': self.article_in_production.pk}

        decorated_func(request, **kwargs)

        # test that the callback was called
        self.assertTrue(func.called,
                        "article_production_user_required decorator wrongly prohibits the production manager from "
                        "accessing an article to which he or she is assigned")

    def test_article_production_user_required_decorator_handles_null_user(self):
        """
        Tests that the article_production_user_required decorator can handle a null request object.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_production_user_required(func)

        request = self.prepare_request_with_user(None, self.journal_one)
        kwargs = {'article_id': self.article_in_production.pk}

        self.assertIsInstance(decorated_func(request, **kwargs), HttpResponseRedirect)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "article_production_user_required decorator incorrectly handles request.user=None")

    def test_article_production_user_required_allows_staff(self):
        """
        Tests that article_production_user_required allows staff to view the article.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_production_user_required(func)

        request = self.prepare_request_with_user(self.admin_user, self.journal_one)
        kwargs = {'article_id': self.article_in_production.pk}

        decorated_func(request, **kwargs)

        # test that the callback was called
        self.assertTrue(func.called,
                        "article_production_user_required decorator wrongly prohibits staff from "
                        "accessing an article in production")

    def test_article_production_user_required_allows_staff_regardless_of_stage(self):
        """
        Tests that article_production_user_required allows staff to view the article in production, regardless of stage.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_production_user_required(func)

        request = self.prepare_request_with_user(self.admin_user, self.journal_one)
        kwargs = {'article_id': self.article_published.pk}

        decorated_func(request, **kwargs)

        # test that the callback was called
        self.assertTrue(func.called,
                        "article_production_user_required decorator wrongly prohibits staff from "
                        "accessing an article that has been published's production stage")

    def test_article_production_user_required_blocks_editor(self):
        """
        Tests that article_production_user_required prohibits an editor from viewing the article production page.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_production_user_required(func)

        request = self.prepare_request_with_user(self.editor, self.journal_one)
        kwargs = {'article_id': self.article_in_production.pk}

        with self.assertRaises(PermissionDenied):
            decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "article_production_user_required decorator wrongly allows an editor to "
                         "access an article in production to which he or she is assigned")

    def test_article_production_user_required_blocks_author(self):
        """
        Tests that article_production_user_required prohibits an author from viewing the article production page.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_production_user_required(func)

        request = self.prepare_request_with_user(self.author, self.journal_one)
        kwargs = {'article_id': self.article_in_production.pk}

        with self.assertRaises(PermissionDenied):
            decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "article_production_user_required decorator wrongly allows an editor to "
                         "access an article in production to which he or she is assigned")

    def test_article_production_user_required_blocks_regular_users(self):
        """
        Tests that article_production_user_required prohibits a regular user from viewing the article production page.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_production_user_required(func)

        request = self.prepare_request_with_user(self.regular_user, self.journal_one)
        kwargs = {'article_id': self.article_in_production.pk}

        with self.assertRaises(PermissionDenied):
            decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "article_production_user_required decorator wrongly allows an editor to "
                         "access an article in production to which he or she is assigned")

    def test_article_production_user_required_blocks_production_when_stage_not_set_to_production(self):
        """
        Tests that article_production_user_required blocks the correct production user when the stage is not set to
        Typesetting.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_production_user_required(func)

        request = self.prepare_request_with_user(self.production, self.journal_one)
        kwargs = {'article_id': self.article_published.pk}

        with self.assertRaises(PermissionDenied):
            decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "article_production_user_required decorator wrongly allows a production manager to "
                         "access an article that is not in production")

    def test_article_production_user_required_decorator_blocks_inactive_users(self):
        """
        Tests that the article_production_user_required decorator does not allow an inactive to view production pages.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_production_user_required(func)

        request = self.prepare_request_with_user(self.inactive_user, self.journal_one)
        kwargs = {'article_id': self.article_published.pk}

        self.assertIsInstance(decorated_func(request, **kwargs), HttpResponseRedirect)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "article_production_user_required decorator wrongly allows inactive users to access "
                         "production content")

    def test_article_production_user_required_decorator_blocks_anonymous_users(self):
        """
        Tests that the production_user_or_editor_required decorator blocks anonymous users.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_production_user_required(func)

        anon_user = AnonymousUser()
        request = self.prepare_request_with_user(anon_user, self.journal_one)
        kwargs = {'article_id': self.article_published.pk}

        self.assertIsInstance(decorated_func(request, **kwargs), HttpResponseRedirect)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "article_production_user_required decorator wrongly allows anonymous users to access "
                         "production content")

    def test_article_production_user_required_allows_assigned_proofing_manager(self):
        """
        Tests that a proofing manager can access the production screen.
        :return:
        """

        proofing_models.ProofingAssignment.objects.create(
            article=self.article_in_proofing,
            proofing_manager=self.proofing_manager
        )

        func = Mock()
        decorated_func = decorators.article_production_user_required(func)

        request = self.prepare_request_with_user(self.proofing_manager, self.journal_one)
        kwargs = {'article_id': self.article_in_proofing.pk}

        decorated_func(request, **kwargs)

        # test that the callback was called
        self.assertTrue(func.called,
                        "article_production_user_required decorator wrongly prohibits proofing manager")

    # Tests for reviewer_user_for_assignment_required
    def test_reviewer_user_for_assignment_required_allows_reviewer(self):
        """
        Tests that reviewer_user_for_assignment_required allows the correct reviewer user to view the article.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.reviewer_user_for_assignment_required(func)

        request = self.prepare_request_with_user(self.second_user, self.journal_one)
        kwargs = {'assignment_id': self.review_assignment.id}

        decorated_func(request, **kwargs)

        # test that the callback was called
        self.assertTrue(func.called,
                        "reviewer_user_for_assignment_required decorator wrongly prohibits the reviewer from "
                        "accessing an article to which he or she is assigned")

    def test_reviewer_user_for_assignment_required_decorator_handles_null_user(self):
        """
        Tests that the reviewer_user_for_assignment_required decorator can handle a null request object.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.reviewer_user_for_assignment_required(func)

        request = self.prepare_request_with_user(None, self.journal_one)
        kwargs = {'assignment_id': self.review_assignment.id}

        self.assertIsInstance(decorated_func(request, **kwargs), HttpResponseRedirect)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "reviewer_user_for_assignment_required decorator incorrectly handles request.user=None")

    def test_reviewer_user_for_assignment_required_allows_staff(self):
        """
        Tests that reviewer_user_for_assignment_required allows staff to view the article.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.reviewer_user_for_assignment_required(func)

        request = self.prepare_request_with_user(self.admin_user, self.journal_one)
        kwargs = {'assignment_id': self.review_assignment.id}

        decorated_func(request, **kwargs)

        # test that the callback was called
        self.assertTrue(func.called,
                        "reviewer_user_for_assignment_required decorator wrongly prohibits staff from "
                        "accessing an article in production")

    def test_reviewer_user_for_assignment_required_allows_staff_regardless_of_stage(self):
        """
        Tests that reviewer_user_for_assignment_required allows staff to article in review, regardless of stage.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.reviewer_user_for_assignment_required(func)

        request = self.prepare_request_with_user(self.admin_user, self.journal_one)
        kwargs = {'assignment_id': self.review_assignment.id}

        decorated_func(request, **kwargs)

        # test that the callback was called
        self.assertTrue(func.called,
                        "reviewer_user_for_assignment_required decorator wrongly prohibits staff from "
                        "accessing an article that has been published's production stage")

    def test_reviewer_user_for_assignment_required_blocks_editor(self):
        """
        Tests that reviewer_user_for_assignment_required prohibits an editor from viewing the article review page.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.reviewer_user_for_assignment_required(func)

        request = self.prepare_request_with_user(self.editor, self.journal_one)
        kwargs = {'assignment_id': self.review_assignment.id}

        with self.assertRaises(PermissionDenied):
            decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "reviewer_user_for_assignment_required decorator wrongly allows an editor to "
                         "access an article in production to which he or she is assigned")

    def test_reviewer_user_for_assignment_required_blocks_author(self):
        """
        Tests that reviewer_user_for_assignment_required prohibits an author from viewing the article review page.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.reviewer_user_for_assignment_required(func)

        request = self.prepare_request_with_user(self.author, self.journal_one)
        kwargs = {'assignment_id': self.review_assignment.id}

        with self.assertRaises(PermissionDenied):
            decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "reviewer_user_for_assignment_required decorator wrongly allows an editor to "
                         "access an article in production to which he or she is assigned")

    def test_reviewer_user_for_assignment_required_blocks_regular_users(self):
        """
        Tests that reviewer_user_for_assignment_required prohibits a regular user from viewing the article review page.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.reviewer_user_for_assignment_required(func)

        request = self.prepare_request_with_user(self.second_reviewer, self.journal_one)
        kwargs = {'assignment_id': self.review_assignment.id}

        with self.assertRaises(PermissionDenied):
            decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "reviewer_user_for_assignment_required decorator wrongly allows an editor to "
                         "access an article in production to which he or she is assigned")

    def test_reviewer_user_for_assignment_required_blocks_review_when_stage_not_set_to_review(self):
        """
        Tests that reviewer_user_for_assignment_required blocks the correct production user when the stage is not set to
        Typesetting.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.reviewer_user_for_assignment_required(func)

        request = self.prepare_request_with_user(self.regular_user, self.journal_one)
        kwargs = {'assignment_id': self.review_assignment_not_in_scope.id}

        with self.assertRaises(PermissionDenied):
            decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "reviewer_user_for_assignment_required decorator wrongly allows a reviewer to "
                         "access an article that is not in a review stage")

    def test_reviewer_user_for_assignment_required_decorator_blocks_inactive_users(self):
        """
        Tests that the reviewer_user_for_assignment_required decorator does not allow an inactive to view reviewer pages
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.reviewer_user_for_assignment_required(func)

        request = self.prepare_request_with_user(self.inactive_user, self.journal_one)
        kwargs = {'assignment_id': self.review_assignment.id}

        self.assertIsInstance(decorated_func(request, **kwargs), HttpResponseRedirect)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "reviewer_user_for_assignment_required decorator wrongly allows inactive users to access "
                         "production content")

    def test_reviewer_user_for_assignment_required_decorator_blocks_anonymous_users(self):
        """
        Tests that the reviewer_user_for_assignment_required decorator blocks anonymous users.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.reviewer_user_for_assignment_required(func)

        anon_user = AnonymousUser()
        request = self.prepare_request_with_user(anon_user, self.journal_one)
        kwargs = {'assignment_id': self.review_assignment.id}

        self.assertIsInstance(decorated_func(request, **kwargs), HttpResponseRedirect)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "reviewer_user_for_assignment_required decorator wrongly allows anonymous users to access "
                         "production content")

    # Tests for article_stage_production_required
    def test_article_stage_production_required_blocks_access_to_published_articles(self):
        """
        Tests that users with access to articles in production cannot access published articles.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_stage_production_required(func)

        anon_user = AnonymousUser()
        request = self.prepare_request_with_user(anon_user, self.journal_one)
        kwargs = {'article_id': self.article_published.pk}

        with self.assertRaises(PermissionDenied):
            # test that production_user_or_editor_required raises a PermissionDenied exception
            decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "article_stage_production_required decorator wrongly allows access to articles that have been"
                         "published")

    def test_article_stage_production_required_blocks_access_to_unsubmitted_articles(self):
        """
        Tests that users with access to articles in production cannot access unsubmitted articles.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_stage_production_required(func)

        anon_user = AnonymousUser()
        request = self.prepare_request_with_user(anon_user, self.journal_one)
        kwargs = {'article_id': self.article_unsubmitted.pk}

        with self.assertRaises(PermissionDenied):
            # test that production_user_or_editor_required raises a PermissionDenied exception
            decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "article_stage_production_required decorator wrongly allows access to articles that are"
                         "unsubmitted")

    def test_article_stage_production_required_blocks_access_to_unassigned_articles(self):
        """
        Tests that users with access to articles in production cannot access unassigned articles.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_stage_production_required(func)

        anon_user = AnonymousUser()
        request = self.prepare_request_with_user(anon_user, self.journal_one)
        kwargs = {'article_id': self.article_unassigned.pk}

        with self.assertRaises(PermissionDenied):
            # test that production_user_or_editor_required raises a PermissionDenied exception
            decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "article_stage_production_required decorator wrongly allows access to articles that are"
                         "unassigned")

    def test_article_stage_production_required_blocks_access_to_assigned_articles(self):
        """
        Tests that users with access to articles in production cannot access assigned articles.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_stage_production_required(func)

        anon_user = AnonymousUser()
        request = self.prepare_request_with_user(anon_user, self.journal_one)
        kwargs = {'article_id': self.article_assigned.pk}

        with self.assertRaises(PermissionDenied):
            # test that production_user_or_editor_required raises a PermissionDenied exception
            decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "article_stage_production_required decorator wrongly allows access to articles that are"
                         "assigned")

    def test_article_stage_production_required_blocks_access_to_under_review_articles(self):
        """
        Tests that users with access to articles in production cannot access articles that are under review.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_stage_production_required(func)

        anon_user = AnonymousUser()
        request = self.prepare_request_with_user(anon_user, self.journal_one)
        kwargs = {'article_id': self.article_under_review.pk}

        with self.assertRaises(PermissionDenied):
            # test that production_user_or_editor_required raises a PermissionDenied exception
            decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "article_stage_production_required decorator wrongly allows access to articles that are"
                         "under review")

    def test_article_stage_production_required_blocks_access_to_under_revision_articles(self):
        """
        Tests that users with access to articles in production cannot access articles that are under revision.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_stage_production_required(func)

        anon_user = AnonymousUser()
        request = self.prepare_request_with_user(anon_user, self.journal_one)
        kwargs = {'article_id': self.article_under_revision.pk}

        with self.assertRaises(PermissionDenied):
            # test that production_user_or_editor_required raises a PermissionDenied exception
            decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "article_stage_production_required decorator wrongly allows access to articles that are"
                         "under revision")

    def test_article_stage_production_required_blocks_access_to_rejected_articles(self):
        """
        Tests that users with access to articles in production cannot access rejected articles.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_stage_production_required(func)

        anon_user = AnonymousUser()
        request = self.prepare_request_with_user(anon_user, self.journal_one)
        kwargs = {'article_id': self.article_rejected.pk}

        with self.assertRaises(PermissionDenied):
            # test that production_user_or_editor_required raises a PermissionDenied exception
            decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "article_stage_production_required decorator wrongly allows access to articles that are"
                         "rejected")

    def test_article_stage_production_required_blocks_access_to_accepted_articles(self):
        """
        Tests that users with access to articles in production cannot access accepted articles.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_stage_production_required(func)

        anon_user = AnonymousUser()
        request = self.prepare_request_with_user(anon_user, self.journal_one)
        kwargs = {'article_id': self.article_accepted.pk}

        with self.assertRaises(PermissionDenied):
            # test that production_user_or_editor_required raises a PermissionDenied exception
            decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "article_stage_production_required decorator wrongly allows access to articles that are"
                         "accepted")

    def test_article_stage_production_required_blocks_access_to_editor_copyediting_articles(self):
        """
        Tests that users with access to articles in production cannot access articles that are in editor copyediting.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_stage_production_required(func)

        anon_user = AnonymousUser()
        request = self.prepare_request_with_user(anon_user, self.journal_one)
        kwargs = {'article_id': self.article_editor_copyediting.pk}

        with self.assertRaises(PermissionDenied):
            # test that production_user_or_editor_required raises a PermissionDenied exception
            decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "article_stage_production_required decorator wrongly allows access to articles that are"
                         "in editor copyediting")

    def test_article_stage_production_required_blocks_access_to_author_copyediting_articles(self):
        """
        Tests that users with access to articles in production cannot access articles that are in author copyediting.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_stage_production_required(func)

        anon_user = AnonymousUser()
        request = self.prepare_request_with_user(anon_user, self.journal_one)
        kwargs = {'article_id': self.article_author_copyediting.pk}

        with self.assertRaises(PermissionDenied):
            # test that production_user_or_editor_required raises a PermissionDenied exception
            decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "article_stage_production_required decorator wrongly allows access to articles that are"
                         "in author copyediting")

    def test_article_stage_production_required_blocks_access_to_final_copyediting_articles(self):
        """
        Tests that users with access to articles in production cannot access articles that are in final copyediting.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_stage_production_required(func)

        anon_user = AnonymousUser()
        request = self.prepare_request_with_user(anon_user, self.journal_one)
        kwargs = {'article_id': self.article_final_copyediting.pk}

        with self.assertRaises(PermissionDenied):
            # test that production_user_or_editor_required raises a PermissionDenied exception
            decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "article_stage_production_required decorator wrongly allows access to articles that are"
                         "in final copyediting")

    def test_article_stage_production_required_blocks_access_to_proofing_articles(self):
        """
        Tests that users with access to articles in production cannot access articles that are in proofing.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_stage_production_required(func)

        anon_user = AnonymousUser()
        request = self.prepare_request_with_user(anon_user, self.journal_one)
        kwargs = {'article_id': self.article_proofing.pk}

        with self.assertRaises(PermissionDenied):
            # test that production_user_or_editor_required raises a PermissionDenied exception
            decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "article_stage_production_required decorator wrongly allows access to articles that are"
                         "in proofing")

    def test_article_stage_production_required_allows_access_to_production_articles(self):
        """
        Tests that users with access to articles in production can access articles that are in production.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_stage_production_required(func)

        anon_user = AnonymousUser()
        request = self.prepare_request_with_user(anon_user, self.journal_one)
        kwargs = {'article_id': self.article_in_production.pk}

        decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertTrue(func.called,
                        "article_stage_production_required decorator wrongly blocks access to articles that are in"
                        "production")

    # Tests for article_stage_accepted_or_later_required
    def test_article_stage_accepted_or_later_required_allows_access_to_published_articles(self):
        """
        Tests that the function that checks if an article is post-acceptance allows access to published articles.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_stage_accepted_or_later_required(func)

        anon_user = AnonymousUser()
        request = self.prepare_request_with_user(anon_user, self.journal_one)
        kwargs = {'identifier': self.article_published.identifier.identifier,
                  'identifier_type': self.article_published.identifier.id_type}

        decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertTrue(func.called,
                        "article_stage_accepted_or_later_required decorator wrongly allows access to articles that are"
                        "published")

    def test_article_stage_accepted_or_later_required_blocks_access_to_unsubmitted_articles(self):
        """
        Tests that the function that checks if an article is post-acceptance blocks access to unsubmitted articles.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_stage_accepted_or_later_required(func)

        anon_user = AnonymousUser()
        request = self.prepare_request_with_user(anon_user, self.journal_one)
        kwargs = {'identifier': self.article_unsubmitted.identifier.identifier,
                  'identifier_type': self.article_unsubmitted.identifier.id_type}

        with self.assertRaises(PermissionDenied):
            # test that production_user_or_editor_required raises a PermissionDenied exception
            decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "article_stage_accepted_or_later_required decorator wrongly allows access to articles that are"
                         "unsubmitted")

    def test_article_stage_accepted_or_later_required_blocks_access_to_unassigned_articles(self):
        """
        Tests that the function that checks if an article is post-acceptance blocks access to unassigned articles.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_stage_accepted_or_later_required(func)

        anon_user = AnonymousUser()
        request = self.prepare_request_with_user(anon_user, self.journal_one)
        kwargs = {'identifier': self.article_unassigned.identifier.identifier,
                  'identifier_type': self.article_unassigned.identifier.id_type}

        with self.assertRaises(PermissionDenied):
            # test that production_user_or_editor_required raises a PermissionDenied exception
            decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "article_stage_accepted_or_later_required decorator wrongly allows access to articles that are"
                         "unassigned")

    def test_article_stage_accepted_or_later_required_blocks_access_to_assigned_articles(self):
        """
        Tests that the function that checks if an article is post-acceptance blocks access to assigned articles.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_stage_accepted_or_later_required(func)

        anon_user = AnonymousUser()
        request = self.prepare_request_with_user(anon_user, self.journal_one)
        kwargs = {'identifier': self.article_assigned.identifier.identifier,
                  'identifier_type': self.article_assigned.identifier.id_type}

        with self.assertRaises(PermissionDenied):
            # test that production_user_or_editor_required raises a PermissionDenied exception
            decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "article_stage_accepted_or_later_required decorator wrongly allows access to articles that are"
                         "assigned")

    def test_article_stage_accepted_or_later_required_blocks_access_to_under_review_articles(self):
        """
        Tests that the function that checks if an article is post-acceptance blocks access to articles that are under
        review.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_stage_accepted_or_later_required(func)

        anon_user = AnonymousUser()
        request = self.prepare_request_with_user(anon_user, self.journal_one)
        kwargs = {'identifier': self.article_under_review.identifier.identifier,
                  'identifier_type': self.article_under_review.identifier.id_type}

        with self.assertRaises(PermissionDenied):
            # test that production_user_or_editor_required raises a PermissionDenied exception
            decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "article_stage_accepted_or_later_required decorator wrongly allows access to articles that are"
                         "under review")

    def test_article_stage_accepted_or_later_required_blocks_access_to_under_revision_articles(self):
        """
        Tests that the function that checks if an article is post-acceptance blocks access to articles that are under
        revision.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_stage_accepted_or_later_required(func)

        anon_user = AnonymousUser()
        request = self.prepare_request_with_user(anon_user, self.journal_one)
        kwargs = {'identifier': self.article_under_revision.identifier.identifier,
                  'identifier_type': self.article_under_revision.identifier.id_type}

        with self.assertRaises(PermissionDenied):
            # test that production_user_or_editor_required raises a PermissionDenied exception
            decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "article_stage_accepted_or_later_required decorator wrongly allows access to articles that are"
                         "under revision")

    def test_article_stage_accepted_or_later_required_blocks_access_to_rejected_articles(self):
        """
        Tests that the function that checks if an article is post-acceptance blocks access to rejected articles.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_stage_accepted_or_later_required(func)

        anon_user = AnonymousUser()
        request = self.prepare_request_with_user(anon_user, self.journal_one)
        kwargs = {'identifier': self.article_rejected.identifier.identifier,
                  'identifier_type': self.article_rejected.identifier.id_type}

        with self.assertRaises(PermissionDenied):
            # test that production_user_or_editor_required raises a PermissionDenied exception
            decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "article_stage_accepted_or_later_required decorator wrongly allows access to articles that are"
                         "rejected")

    def test_article_stage_accepted_or_later_required_allows_access_to_accepted_articles(self):
        """
        Tests that the function that checks if an article is post-acceptance allows access to accepted articles.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_stage_accepted_or_later_required(func)

        anon_user = AnonymousUser()
        request = self.prepare_request_with_user(anon_user, self.journal_one)
        kwargs = {'identifier': self.article_accepted.identifier.identifier,
                  'identifier_type': self.article_accepted.identifier.id_type}

        decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertTrue(func.called,
                        "article_stage_accepted_or_later_required decorator wrongly blocks access to articles that are"
                        "accepted")

    def test_article_stage_accepted_or_later_required_allows_access_to_editor_copyediting_articles(self):
        """
        Tests that the function that checks if an article is post-acceptance allows access to editor copyediting
        articles.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_stage_accepted_or_later_required(func)

        anon_user = AnonymousUser()
        request = self.prepare_request_with_user(anon_user, self.journal_one)
        kwargs = {'identifier': self.article_editor_copyediting.identifier.identifier,
                  'identifier_type': self.article_editor_copyediting.identifier.id_type}

        decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertTrue(func.called,
                        "article_stage_accepted_or_later_required decorator wrongly blocks access to articles that are"
                        "in editor copyediting")

    def test_article_stage_accepted_or_later_required_allows_access_to_author_copyediting_articles(self):
        """
        Tests that the function that checks if an article is post-acceptance allows access to author copyediting
        articles.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_stage_accepted_or_later_required(func)

        anon_user = AnonymousUser()
        request = self.prepare_request_with_user(anon_user, self.journal_one)
        kwargs = {'identifier': self.article_author_copyediting.identifier.identifier,
                  'identifier_type': self.article_author_copyediting.identifier.id_type}

        decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertTrue(func.called,
                        "article_stage_accepted_or_later_required decorator wrongly blocks access to articles that are"
                        "in author copyediting")

    def test_article_stage_accepted_or_later_required_allows_access_to_final_copyediting_articles(self):
        """
        Tests that the function that checks if an article is post-acceptance allows access to final copyediting
        articles.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_stage_accepted_or_later_required(func)

        anon_user = AnonymousUser()
        request = self.prepare_request_with_user(anon_user, self.journal_one)
        kwargs = {'identifier': self.article_final_copyediting.identifier.identifier,
                  'identifier_type': self.article_final_copyediting.identifier.id_type}

        decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertTrue(func.called,
                        "article_stage_accepted_or_later_required decorator wrongly blocks access to articles that are"
                        "in final copyediting")

    def test_article_stage_accepted_or_later_required_allows_access_to_proofing_articles(self):
        """
        Tests that the function that checks if an article is post-acceptance allows access to proofing articles.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_stage_accepted_or_later_required(func)

        anon_user = AnonymousUser()
        request = self.prepare_request_with_user(anon_user, self.journal_one)
        kwargs = {'identifier': self.article_proofing.identifier.identifier,
                  'identifier_type': self.article_proofing.identifier.id_type}

        decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertTrue(func.called,
                        "article_stage_accepted_or_later_required decorator wrongly blocks access to articles that are"
                        "in proofing")

    def test_article_stage_accepted_or_later_required_allows_access_to_production_articles(self):
        """
        Tests that the function that checks if an article is post-acceptance allows access to production articles.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_stage_accepted_or_later_required(func)

        anon_user = AnonymousUser()
        request = self.prepare_request_with_user(anon_user, self.journal_one)
        kwargs = {'identifier': self.article_in_production.identifier.identifier,
                  'identifier_type': self.article_in_production.identifier.id_type}

        decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertTrue(func.called,
                        "article_stage_accepted_or_later_required decorator wrongly blocks access to articles that are"
                        "in production")

    # Tests for article_stage_accepted_or_later_or_staff_required
    def test_article_stage_accepted_or_later_or_staff_required_allows_access_to_published_articles(self):
        """
        Tests that the function that checks if an article is post-acceptance allows access to published articles.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_stage_accepted_or_later_or_staff_required(func)

        anon_user = AnonymousUser()
        request = self.prepare_request_with_user(anon_user, self.journal_one)
        kwargs = {'identifier': self.article_published.identifier.identifier,
                  'identifier_type': self.article_published.identifier.id_type}

        decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertTrue(func.called,
                        "article_stage_accepted_or_later_required decorator wrongly allows access to articles that are"
                        "published")

    def test_article_stage_accepted_or_later_or_staff_required_blocks_access_to_unsubmitted_articles(self):
        """
        Tests that the function that checks if an article is post-acceptance blocks access to unsubmitted articles.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_stage_accepted_or_later_or_staff_required(func)

        anon_user = AnonymousUser()
        request = self.prepare_request_with_user(anon_user, self.journal_one)
        kwargs = {'identifier': self.article_unsubmitted.identifier.identifier,
                  'identifier_type': self.article_unsubmitted.identifier.id_type}

        with self.assertRaises(PermissionDenied):
            # test that production_user_or_editor_required raises a PermissionDenied exception
            decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "article_stage_accepted_or_later_required decorator wrongly allows access to articles that are"
                         "unsubmitted")

    def test_article_stage_accepted_or_later_or_staff_required_blocks_access_to_unassigned_articles(self):
        """
        Tests that the function that checks if an article is post-acceptance blocks access to unassigned articles.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_stage_accepted_or_later_or_staff_required(func)

        anon_user = AnonymousUser()
        request = self.prepare_request_with_user(anon_user, self.journal_one)
        kwargs = {'identifier': self.article_unassigned.identifier.identifier,
                  'identifier_type': self.article_unassigned.identifier.id_type}

        with self.assertRaises(PermissionDenied):
            # test that production_user_or_editor_required raises a PermissionDenied exception
            decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "article_stage_accepted_or_later_required decorator wrongly allows access to articles that are"
                         "unassigned")

    def test_article_stage_accepted_or_later_or_staff_required_blocks_access_to_assigned_articles(self):
        """
        Tests that the function that checks if an article is post-acceptance blocks access to assigned articles.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_stage_accepted_or_later_or_staff_required(func)

        anon_user = AnonymousUser()
        request = self.prepare_request_with_user(anon_user, self.journal_one)
        kwargs = {'identifier': self.article_assigned.identifier.identifier,
                  'identifier_type': self.article_assigned.identifier.id_type}

        with self.assertRaises(PermissionDenied):
            # test that production_user_or_editor_required raises a PermissionDenied exception
            decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "article_stage_accepted_or_later_required decorator wrongly allows access to articles that are"
                         "assigned")

    def test_article_stage_accepted_or_later_or_staff_required_blocks_access_to_under_review_articles(self):
        """
        Tests that the function that checks if an article is post-acceptance blocks access to articles that are under
        review.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_stage_accepted_or_later_or_staff_required(func)

        anon_user = AnonymousUser()
        request = self.prepare_request_with_user(anon_user, self.journal_one)
        kwargs = {'identifier': self.article_under_review.identifier.identifier,
                  'identifier_type': self.article_under_review.identifier.id_type}

        with self.assertRaises(PermissionDenied):
            # test that production_user_or_editor_required raises a PermissionDenied exception
            decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "article_stage_accepted_or_later_required decorator wrongly allows access to articles that are"
                         "under review")

    def test_article_stage_accepted_or_later_or_staff_required_blocks_access_to_under_revision_articles(self):
        """
        Tests that the function that checks if an article is post-acceptance blocks access to articles that are under
        revision.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_stage_accepted_or_later_or_staff_required(func)

        anon_user = AnonymousUser()
        request = self.prepare_request_with_user(anon_user, self.journal_one)
        kwargs = {'identifier': self.article_under_revision.identifier.identifier,
                  'identifier_type': self.article_under_revision.identifier.id_type}

        with self.assertRaises(PermissionDenied):
            # test that production_user_or_editor_required raises a PermissionDenied exception
            decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "article_stage_accepted_or_later_required decorator wrongly allows access to articles that are"
                         "under revision")

    def test_article_stage_accepted_or_later_or_staff_allows_staff_access_to_rejected_articles(self):
        """
        Tests that the function that checks if an article is post-acceptance allows staff access to rejected articles.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_stage_accepted_or_later_or_staff_required(func)

        request = self.prepare_request_with_user(self.admin_user, self.journal_one)
        kwargs = {'identifier': self.article_rejected.identifier.identifier,
                  'identifier_type': self.article_rejected.identifier.id_type}

        # test that production_user_or_editor_required raises a PermissionDenied exception
        decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertTrue(func.called, "article_stage_accepted_or_later_or_staff_required decorator wrongly blocks staff "
                                     "access to articles that are rejected")

    def test_article_stage_accepted_or_later_or_staff_required_blocks_access_to_rejected_articles(self):
        """
        Tests that the function that checks if an article is post-acceptance blocks access to rejected articles.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_stage_accepted_or_later_or_staff_required(func)

        anon_user = AnonymousUser()
        request = self.prepare_request_with_user(anon_user, self.journal_one)
        kwargs = {'identifier': self.article_rejected.identifier.identifier,
                  'identifier_type': self.article_rejected.identifier.id_type}

        with self.assertRaises(PermissionDenied):
            # test that production_user_or_editor_required raises a PermissionDenied exception
            decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "article_stage_accepted_or_later_required decorator wrongly allows access to articles that are"
                         "rejected")

    def test_article_stage_accepted_or_later_or_staff_required_allows_access_to_accepted_articles(self):
        """
        Tests that the function that checks if an article is post-acceptance allows access to accepted articles.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_stage_accepted_or_later_or_staff_required(func)

        anon_user = AnonymousUser()
        request = self.prepare_request_with_user(anon_user, self.journal_one)
        kwargs = {'identifier': self.article_accepted.identifier.identifier,
                  'identifier_type': self.article_accepted.identifier.id_type}

        decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertTrue(func.called,
                        "article_stage_accepted_or_later_required decorator wrongly blocks access to articles that are"
                        "accepted")

    def test_article_stage_accepted_or_later_or_staff_required_allows_access_to_editor_copyediting_articles(self):
        """
        Tests that the function that checks if an article is post-acceptance allows access to editor copyediting
        articles.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_stage_accepted_or_later_or_staff_required(func)

        anon_user = AnonymousUser()
        request = self.prepare_request_with_user(anon_user, self.journal_one)
        kwargs = {'identifier': self.article_editor_copyediting.identifier.identifier,
                  'identifier_type': self.article_editor_copyediting.identifier.id_type}

        decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertTrue(func.called,
                        "article_stage_accepted_or_later_required decorator wrongly blocks access to articles that are"
                        "in editor copyediting")

    def test_article_stage_accepted_or_later_or_staff_required_allows_access_to_author_copyediting_articles(self):
        """
        Tests that the function that checks if an article is post-acceptance allows access to author copyediting
        articles.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_stage_accepted_or_later_or_staff_required(func)

        anon_user = AnonymousUser()
        request = self.prepare_request_with_user(anon_user, self.journal_one)
        kwargs = {'identifier': self.article_author_copyediting.identifier.identifier,
                  'identifier_type': self.article_author_copyediting.identifier.id_type}

        decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertTrue(func.called,
                        "article_stage_accepted_or_later_required decorator wrongly blocks access to articles that are"
                        "in author copyediting")

    def test_article_stage_accepted_or_later_or_staff_required_allows_access_to_final_copyediting_articles(self):
        """
        Tests that the function that checks if an article is post-acceptance allows access to final copyediting
        articles.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_stage_accepted_or_later_or_staff_required(func)

        anon_user = AnonymousUser()
        request = self.prepare_request_with_user(anon_user, self.journal_one)
        kwargs = {'identifier': self.article_final_copyediting.identifier.identifier,
                  'identifier_type': self.article_final_copyediting.identifier.id_type}

        decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertTrue(func.called,
                        "article_stage_accepted_or_later_required decorator wrongly blocks access to articles that are"
                        "in final copyediting")

    def test_article_stage_accepted_or_later_or_staff_required_allows_access_to_proofing_articles(self):
        """
        Tests that the function that checks if an article is post-acceptance allows access to proofing articles.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_stage_accepted_or_later_or_staff_required(func)

        anon_user = AnonymousUser()
        request = self.prepare_request_with_user(anon_user, self.journal_one)
        kwargs = {'identifier': self.article_proofing.identifier.identifier,
                  'identifier_type': self.article_proofing.identifier.id_type}

        decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertTrue(func.called,
                        "article_stage_accepted_or_later_required decorator wrongly blocks access to articles that are"
                        "in proofing")

    def test_article_stage_accepted_or_later_or_staff_required_allows_access_to_production_articles(self):
        """
        Tests that the function that checks if an article is post-acceptance allows access to production articles.
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_stage_accepted_or_later_or_staff_required(func)

        anon_user = AnonymousUser()
        request = self.prepare_request_with_user(anon_user, self.journal_one)
        kwargs = {'identifier': self.article_in_production.identifier.identifier,
                  'identifier_type': self.article_in_production.identifier.id_type}

        decorated_func(request, **kwargs)

        # test that the callback was called
        self.assertTrue(func.called,
                        "article_stage_accepted_or_later_required decorator wrongly blocks access to articles that are"
                        "in production")

    # Tests for article_edit_user_required
    def test_article_edit_user_required_allows_access_to_production_articles(self):
        """
        Tests that a user can edit a specific article in the production stage
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_edit_user_required(func)

        request = self.prepare_request_with_user(self.regular_user, self.journal_one)
        kwargs = {'article_id': self.article_in_production.id}

        decorated_func(request, **kwargs)

        # test that the callback was called
        self.assertTrue(func.called, "article_edit_user_required decorator wrongly blocks access to articles that are "
                                     "in production")

    def test_article_edit_user_required_allows_staff_access_to_production_articles(self):
        """
        Tests that a staff user can edit a specific article in the production stage
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_edit_user_required(func)

        request = self.prepare_request_with_user(self.admin_user, self.journal_one)
        kwargs = {'article_id': self.article_in_production.id}

        decorated_func(request, **kwargs)

        # test that the callback was called
        self.assertTrue(func.called, "article_edit_user_required decorator wrongly blocks staff access to articles that"
                                     " are in production")

    def test_article_edit_user_required_allows_staff_access_to_published_articles(self):
        """
        Tests that a staff user can edit a specific article in the published stage
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_edit_user_required(func)

        request = self.prepare_request_with_user(self.admin_user, self.journal_one)
        kwargs = {'article_id': self.article_published.id}

        decorated_func(request, **kwargs)

        # test that the callback was called
        self.assertTrue(func.called, "article_edit_user_required decorator wrongly blocks staff access to articles that"
                                     " are published")

    def test_article_edit_user_required_allows_staff_access_to_rejected_articles(self):
        """
        Tests that a staff user can edit a specific article in the rejected stage
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_edit_user_required(func)

        request = self.prepare_request_with_user(self.admin_user, self.journal_one)
        kwargs = {'article_id': self.article_rejected.id}

        decorated_func(request, **kwargs)

        # test that the callback was called
        self.assertTrue(func.called, "article_edit_user_required decorator wrongly blocks staff access to articles that"
                                     " are rejected")

    def test_article_edit_user_required_blocks_access_to_production_articles_if_no_user(self):
        """
        Tests that an anonymous user cannot edit a specific article in the production stage
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_edit_user_required(func)

        request = self.prepare_request_with_user(AnonymousUser(), self.journal_one)
        kwargs = {'article_id': self.article_published.id}

        with self.assertRaises(PermissionDenied):
            # test that production_user_or_editor_required raises a PermissionDenied exception
            decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "article_edit_user_required decorator wrongly allows anonymous access to articles that are "
                         "in production")

    def test_article_edit_user_required_blocks_access_to_articles_if_not_owner(self):
        """
        Tests that a user cannot edit an article in production that is not owned by the current user
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_edit_user_required(func)

        request = self.prepare_request_with_user(self.second_user, self.journal_one)
        kwargs = {'article_id': self.article_in_production.id}

        with self.assertRaises(PermissionDenied):
            # test that production_user_or_editor_required raises a PermissionDenied exception
            decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "article_edit_user_required decorator wrongly allows access to articles that are "
                         "in production and not owned by the current user")

    def test_article_edit_user_required_blocks_access_to_published_articles(self):
        """
        Tests that a user cannot edit a specific article in the published stage
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_edit_user_required(func)

        request = self.prepare_request_with_user(self.regular_user, self.journal_one)
        kwargs = {'article_id': self.article_published.id}

        with self.assertRaises(PermissionDenied):
            # test that production_user_or_editor_required raises a PermissionDenied exception
            decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "article_edit_user_required decorator wrongly allows access to articles that are "
                         "published")

    def test_article_edit_user_required_blocks_access_to_rejected_articles(self):
        """
        Tests that a user cannot edit a specific article in the rejected stage
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_edit_user_required(func)

        request = self.prepare_request_with_user(self.regular_user, self.journal_one)
        kwargs = {'article_id': self.article_rejected.id}

        with self.assertRaises(PermissionDenied):
            # test that production_user_or_editor_required raises a PermissionDenied exception
            decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "article_edit_user_required decorator wrongly allows access to articles that are "
                         "rejected")

    # Tests for file_user_required
    def test_file_user_required_blocks_access_to_anonymous_users_to_private_files(self):
        """
        Tests that an anonymous user cannot access private files
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.file_user_required(func)

        request = self.prepare_request_with_user(AnonymousUser(), self.journal_one)
        kwargs = {'file_id': self.private_file.id}

        with self.assertRaises(PermissionDenied):
            # test that production_user_or_editor_required raises a PermissionDenied exception
            decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertFalse(func.called, "file_user_required is erroneously allowing anonymous users access to private "
                                      "files")

    def test_file_user_required_allows_access_to_anonymous_users_to_public_files(self):
        """
        Tests that an anonymous user can access public files
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.file_user_required(func)

        request = self.prepare_request_with_user(AnonymousUser(), self.journal_one)
        kwargs = {'file_id': self.public_file.id}

        decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertTrue(func.called, "file_user_required is erroneously blocking anonymous users access to public "
                                     "files")

    def test_file_user_required_allows_access_to_owners_to_private_files(self):
        """
        Tests that an owner users can access private files
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.file_user_required(func)

        request = self.prepare_request_with_user(self.regular_user, self.journal_one)
        kwargs = {'file_id': self.private_file.id}

        decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertTrue(func.called, "file_user_required is erroneously blocking owner users access to private files")

    def test_file_user_required_allows_staff_access_to_private_files(self):
        """
        Tests that staff users can access private files
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.file_user_required(func)

        request = self.prepare_request_with_user(self.admin_user, self.journal_one)
        kwargs = {'file_id': self.private_file.id}

        decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertTrue(func.called, "file_user_required is erroneously blocking staff users access to private files")

    # Tests for file_edit_user_required
    def test_file_edit_user_required_blocks_access_to_anonymous_users(self):
        """
        Tests that an anonymous user cannot edit files
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.file_edit_user_required(func)

        request = self.prepare_request_with_user(AnonymousUser(), self.journal_one)
        kwargs = {'file_id': self.public_file.id,
                  'identifier': self.article_in_production.identifier.identifier,
                  'identifier_type': self.article_in_production.identifier.id_type
                  }

        with self.assertRaises(PermissionDenied):
            # test that production_user_or_editor_required raises a PermissionDenied exception
            decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertFalse(func.called, "file_user_required is erroneously allowing anonymous users edit access to files")

    def test_file_edit_user_required_allows_access_to_owners_to_private_files(self):
        """
        Tests that an owner users can access private files
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.file_edit_user_required(func)

        request = self.prepare_request_with_user(self.regular_user, self.journal_one)
        kwargs = {'file_id': self.private_file.id,
                  'identifier': self.article_in_production.identifier.identifier,
                  'identifier_type': self.article_in_production.identifier.id_type
                  }

        decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertTrue(func.called, "file_user_required is erroneously blocking owner users access to private files")

    def test_file_edit_user_required_blocks_access_to_non_owners_to_files(self):
        """
        Tests that an owner users can access private files
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.file_edit_user_required(func)

        request = self.prepare_request_with_user(self.second_user, self.journal_one)
        kwargs = {'file_id': self.private_file.id,
                  'identifier': self.article_in_production.identifier.identifier,
                  'identifier_type': self.article_in_production.identifier.id_type
                  }

        with self.assertRaises(PermissionDenied):
            # test that this throws a PermissionDenied error
            decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertFalse(func.called, "file_user_required is erroneously allowing non-owner users edit access to files")

    def test_file_edit_user_required_allows_staff_access_to_files(self):
        """
        Tests that staff users can access private files
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.file_edit_user_required(func)

        request = self.prepare_request_with_user(self.admin_user, self.journal_one)
        kwargs = {'file_id': self.private_file.id,
                  'identifier': self.article_in_production.identifier.identifier,
                  'identifier_type': self.article_in_production.identifier.id_type
                  }

        decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertTrue(func.called, "file_user_required is erroneously blocking staff users access to private files")

    # Test for data_figure_file
    def test_data_figure_file_correctly_identifies_data_figure_file(self):
        """
        Tests that data_figure_file correctly identifies a figure
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.data_figure_file(func)

        request = self.prepare_request_with_user(self.admin_user, self.journal_one)
        kwargs = {'file_id': self.public_file.id,
                  'identifier': self.article_in_production.identifier.identifier,
                  'identifier_type': self.article_in_production.identifier.id_type
                  }

        decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertTrue(func.called, "data_figure_file is not correctly identifying data/figure files")

    def test_data_figure_file_does_not_falsely_identify_data_figure_file(self):
        """
        Tests that data_figure_file correctly identifies a figure
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.data_figure_file(func)

        request = self.prepare_request_with_user(self.admin_user, self.journal_one)
        kwargs = {'file_id': self.private_file.id,
                  'identifier': self.article_in_production.identifier.identifier,
                  'identifier_type': self.article_in_production.identifier.id_type
                  }

        with self.assertRaises(PermissionDenied):
            # test that this throws a PermissionDenied error
            decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertFalse(func.called, "data_figure_file is falsely identifying data/figure files")

    # Tests for has_request
    def test_has_request_works_when_request_present(self):
        """
        Tests that has_request works when a request object is present
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.has_request(func)

        request = self.prepare_request_with_user(self.admin_user, self.journal_one)
        kwargs = {'file_id': self.private_file.id,
                  'identifier': self.article_in_production.identifier.identifier,
                  'identifier_type': self.article_in_production.identifier.id_type
                  }

        decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertTrue(func.called, "has_request fails even when a request is present")

    def test_has_request_fails_when_request_absent(self):
        """
        Tests that has_request doesn't when a request object is absent
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.has_request(func)

        with self.assertRaises(Http404):
            # test that this throws a PermissionDenied error
            decorated_func(None, None)

        # test that the callback was not called
        self.assertFalse(func.called, "has_request is succeeded even when a request is absent")

    # Tests for has_journal
    def test_has_journal_works_when_journal_present(self):
        """
        Tests that has_journal works when a journal object is present
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.has_journal(func)

        request = self.prepare_request_with_user(self.admin_user, self.journal_one)
        kwargs = {'file_id': self.private_file.id,
                  'identifier': self.article_in_production.identifier.identifier,
                  'identifier_type': self.article_in_production.identifier.id_type
                  }

        decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertTrue(func.called, "has_journal fails even when a journal is present")

    def test_has_journal_fails_when_journal_absent(self):
        """
        Tests that has_journal doesn't when a journal object is absent
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.has_journal(func)

        request = self.prepare_request_with_user(self.admin_user, self.journal_one)
        kwargs = {'file_id': self.private_file.id,
                  'identifier': self.article_in_production.identifier.identifier,
                  'identifier_type': self.article_in_production.identifier.id_type
                  }

        request.journal = None

        with self.assertRaises(Http404):
            # test that this throws an Http404 error
            decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertFalse(func.called, "has_journal is succeeded even when a journal is absent")

    # Tests for article_exists
    def test_article_exists_works_when_article_exists(self):
        """
        Tests that article_exists works when the article exists
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.article_exists(func)

        request = self.prepare_request_with_user(self.admin_user, self.journal_one)
        kwargs = {'file_id': self.private_file.id,
                  'identifier': self.article_in_production.identifier.identifier,
                  'identifier_type': self.article_in_production.identifier.id_type
                  }

        decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertTrue(func.called, "article_exists is failing when the article exists")

    def test_article_exists_fails_when_article_does_not_exist(self):
        """
        Tests that article_exists fails when the article does not exist
        :return: None or raises an assertion
        """
        func = Mock()
        decorated_func = decorators.has_journal(func)

        request = self.prepare_request_with_user(self.admin_user, self.journal_one)
        kwargs = {'file_id': self.private_file.id,
                  'identifier': 1337,
                  'identifier_type': self.article_in_production.identifier.id_type
                  }

        request.journal = None

        with self.assertRaises(Http404):
            # test that this throws an Http404 error
            decorated_func(request, **kwargs)

        # test that the callback was not called
        self.assertFalse(func.called, "article_exists is erroneously succeeding when the article does not exist")

    def test_article_decision_not_made(self):
        """
        Tests that an article has not been accepted or declined.
        :return: None or raises an assertion
        """

        func = Mock()
        decorated_func = decorators.article_decision_not_made(func)

        request = self.prepare_request_with_user(self.admin_user, self.journal_one)
        kwargs_article_id = {'article_id': self.article_review_completed.id}
        kwargs_review_id = {'review_id': self.review_assignment_complete.id}

        expected_redirect_url = reverse('review_in_review', kwargs={'article_id': self.article_review_completed.id})
        article_test = decorated_func(request, **kwargs_article_id).url
        review_test = decorated_func(request, **kwargs_review_id).url

        self.assertEqual(article_test, expected_redirect_url)
        self.assertEqual(review_test, expected_redirect_url)

    def test_article_author_required_with_author(self):
        """
        Tests that a user owns an article and that they have the author role
        :return: None or raises an assertion
        """

        func = Mock()
        decorated_func = decorators.article_author_required(func)

        request = self.prepare_request_with_user(self.author, self.journal_one)
        kwargs_article_id = {'article_id': self.article_author_is_owner.id}
        decorated_func(request, **kwargs_article_id)

        self.assertTrue(func.called, 'User is an author')

        # Test with user who does not have role

    def test_article_author_required_with_wrong_author(self):
        func = Mock()
        decorated_func = decorators.article_author_required(func)

        request = self.prepare_request_with_user(self.production, self.journal_one)
        kwargs_article_id = {'article_id': self.article_author_is_owner.id}

        with self.assertRaises(PermissionDenied):
            # test that this throws a PermissionDenied error
            decorated_func(request, **kwargs_article_id)

    def test_copyeditor_user_required(self):
        func = Mock()
        decorated_func = decorators.copyeditor_user_required(func)

        request = self.prepare_request_with_user(self.copyeditor, self.journal_one)

        # call this function which should not throw an error this time
        decorated_func(request)

        # test that the callback was called
        self.assertTrue(func.called,
                        "copyeditor_user_required decorator wrongly prohibits staff from accessing content")

    def test_copyeditor_user_required_allows_staff(self):
        func = Mock()
        decorated_func = decorators.copyeditor_user_required(func)

        request = self.prepare_request_with_user(self.admin_user, self.journal_one)

        # call this function which should not throw an error this time
        decorated_func(request)

        # test that the callback was called
        self.assertTrue(func.called,
                        "copyeditor_user_required decorator wrongly prohibits staff from accessing content")

    def test_copyeditor_user_required_with_null_user(self):
        func = Mock()
        decorated_func = decorators.copyeditor_user_required(func)

        request = self.prepare_request_with_user(None, self.journal_one)

        self.assertIsInstance(decorated_func(request), HttpResponseRedirect)

    def test_copyeditor_user_required_blocks_non_copyeditor(self):
        func = Mock()
        decorated_func = decorators.copyeditor_user_required(func)

        request = self.prepare_request_with_user(self.production, self.journal_one)

        with self.assertRaises(PermissionDenied):
            # test that this throws a PermissionDenied error
            decorated_func(request)

    def test_copyeditor_for_copyedit(self):
        func = Mock()
        decorated_func = decorators.copyeditor_for_copyedit_required(func)
        kwargs = {'copyedit_id': self.copyedit_assignment.pk}

        request = self.prepare_request_with_user(self.copyeditor, self.journal_one)

        decorated_func(request, **kwargs)

        self.assertTrue(func.called,
                        "copyeditor_for_copyedit_required wrongly prohibits copyeditor from accessing content")

    def test_copyeditor_for_copyedit_with_author(self):
        func = Mock()
        decorated_func = decorators.copyeditor_for_copyedit_required(func)
        kwargs = {'copyedit_id': self.copyedit_assignment.pk}

        request = self.prepare_request_with_user(self.author, self.journal_one)

        with self.assertRaises(PermissionDenied):
            decorated_func(request, **kwargs)

    def test_copyeditor_for_copyedit_with_staff(self):
        func = Mock()
        decorated_func = decorators.copyeditor_for_copyedit_required(func)
        kwargs = {'copyedit_id': self.copyedit_assignment.pk}

        request = self.prepare_request_with_user(self.admin_user, self.journal_one)

        decorated_func(request, **kwargs)

        self.assertTrue(func.called,
                        "copyeditor_for_copyedit_required wrongly prohibits admin from accessing content")

    def test_typesetter_user_required_with_typesetter(self):
        func = Mock()
        decorated_func = decorators.typesetter_user_required(func)
        kwargs = {'typeset_id': self.typeset_task.pk}

        request = self.prepare_request_with_user(self.typesetter, self.journal_one)

        decorated_func(request, **kwargs)
        self.assertTrue(func.called,
                        "typesetter_user_required wrongly prohibits typesetter from accessing content")

    def test_typesetter_user_required_with_copyeditor(self):
        func = Mock()
        decorated_func = decorators.typesetter_user_required(func)
        kwargs = {'typeset_id': self.typeset_task.pk}

        request = self.prepare_request_with_user(self.copyeditor, self.journal_one)

        with self.assertRaises(PermissionDenied):
            decorated_func(request, **kwargs)

    def test_typesetter_or_editor_with_typesetter(self):
        func = Mock()
        decorated_func = decorators.typesetter_or_editor_required(func)
        kwargs = {'typeset_id': self.typeset_task.pk}

        request = self.prepare_request_with_user(self.typesetter, self.journal_one)

        decorated_func(request, **kwargs)
        self.assertTrue(func.called,
                        "typesetter_user_required wrongly prohibits typesetter from accessing content")

    def test_typesetter_or_editor_with_copyeditor(self):
        func = Mock()
        decorated_func = decorators.typesetter_or_editor_required(func)
        kwargs = {'typeset_id': self.typeset_task.pk}

        request = self.prepare_request_with_user(self.copyeditor, self.journal_one)

        with self.assertRaises(PermissionDenied):
            decorated_func(request, **kwargs)

    def test_typesetter_or_editor_with_other_typesetter(self):
        func = Mock()
        decorated_func = decorators.typesetter_or_editor_required(func)
        kwargs = {'typeset_id': self.typeset_task.pk}

        request = self.prepare_request_with_user(self.other_typesetter, self.journal_one)

        with self.assertRaises(PermissionDenied):
            decorated_func(request, **kwargs)

    def test_typesetter_or_editor_with_other_editor(self):
        func = Mock()
        decorated_func = decorators.typesetter_or_editor_required(func)
        kwargs = {'typeset_id': self.typeset_task.pk}

        request = self.prepare_request_with_user(self.editor, self.journal_one)

        decorated_func(request, **kwargs)
        self.assertTrue(func.called,
                        "typesetter_or_editor wrongly prohibits editor from accessing content")

    def test_proofing_manager_or_editor_required_with_proofing_manager(self):
        func = Mock()
        decorated_func = decorators.proofing_manager_or_editor_required(func)

        request = self.prepare_request_with_user(self.proofing_manager, self.journal_one)

        decorated_func(request)
        self.assertTrue(func.called,
                        "proofing_manager_or_editor_required, wrongly prohibits manager or editor from content")

    def test_proofing_manager_or_editor_required_with_typesetter(self):
        func = Mock()
        decorated_func = decorators.proofing_manager_or_editor_required(func)

        request = self.prepare_request_with_user(self.typesetter, self.journal_one)

        with self.assertRaises(PermissionDenied):
            decorated_func(request)

    def test_proofing_manager_for_article_required(self):
        func = Mock()
        decorated_func = decorators.proofing_manager_for_article_required(func)
        kwargs = {'article_id': self.article_proofing.pk}

        request = self.prepare_request_with_user(self.proofing_manager, self.journal_one)

        decorated_func(request, **kwargs)
        self.assertTrue(func.called,
                        "proofing_manager_for_article_required, wrongly prohibits manager or editor from content")

    def test_proofing_manager_for_article_required_without_manager(self):
        func = Mock()
        decorated_func = decorators.proofing_manager_for_article_required(func)
        kwargs = {'article_id': self.article_proofing.pk}

        request = self.prepare_request_with_user(self.regular_user, self.journal_one)

        with self.assertRaises(PermissionDenied):
            print(decorated_func(request, **kwargs))

    def test_proofreader_or_typesetter_required(self):
        func = Mock()
        decorated_func = decorators.proofreader_or_typesetter_required(func)

        request_one = self.prepare_request_with_user(self.proofreader, self.journal_one)
        request_two = self.prepare_request_with_user(self.typesetter, self.journal_one)

        decorated_func(request_one)
        self.assertTrue(func.called,
                        "proofreader_or_typesetter_required, wrongly prohibits proofreader or editor from content")

        decorated_func(request_two)
        self.assertTrue(func.called,
                        "proofreader_or_typesetter_required, wrongly prohibits typesetter or editor from content")

    def test_proofreader_or_typesetter_required_with_copyeditor(self):
        func = Mock()
        decorated_func = decorators.proofreader_or_typesetter_required(func)

        request = self.prepare_request_with_user(self.copyeditor, self.journal_one)

        with self.assertRaises(PermissionDenied):
            decorated_func(request)

    def test_proofreader_for_article_required(self):
        func = Mock()
        decorated_func = decorators.proofreader_for_article_required(func)
        kwargs = {'proofing_task_id': self.proofing_task.pk}

        request = self.prepare_request_with_user(self.proofreader, self.journal_one)

        decorated_func(request, **kwargs)
        self.assertTrue(func.called,
                        "proofreader_for_article_required, wrongly prohibits proofreader from content")

    def test_proofreader_for_article_required_with_author_proofreader(self):
        func = Mock()
        decorated_func = decorators.proofreader_for_article_required(func)

        author_proofing_task = proofing_models.ProofingTask(
                round=self.proofing_assignment.current_proofing_round(),
                proofreader=self.author,
                notified=True,
                due=timezone.now(),
                accepted=timezone.now(),
                task='author_task')
        author_proofing_task.save()

        kwargs = {'proofing_task_id': author_proofing_task.pk}

        request = self.prepare_request_with_user(self.author, self.journal_one)

        decorated_func(request, **kwargs)
        self.assertTrue(func.called,
                        "proofreader_for_article_required, wrongly prohibits "
                        "author proofreader from content")

    def test_proofreader_for_article_required_with_bad_proofreader(self):
        func = Mock()
        decorated_func = decorators.proofreader_for_article_required(func)
        kwargs = {'proofing_task_id': self.proofing_task.pk}

        request = self.prepare_request_with_user(self.proofreader_two, self.journal_one)

        with self.assertRaises(PermissionDenied):
            decorated_func(request, **kwargs)

    def test_typesetter_for_corrections_required(self):
        func = Mock()
        decorated_func = decorators.typesetter_for_corrections_required(func)
        kwargs = {'typeset_task_id': self.correction_task.pk}

        request = self.prepare_request_with_user(self.typesetter, self.journal_one)

        decorated_func(request, **kwargs)
        self.assertTrue(func.called,
                        "typesetter_for_corrections_required, wrongly prohibits typesetter from content")

    def test_typesetter_for_corrections_required_with_bad_typesetter(self):
        func = Mock()
        decorated_func = decorators.typesetter_for_corrections_required(func)
        kwargs = {'typeset_task_id': self.correction_task.pk}

        request = self.prepare_request_with_user(self.other_typesetter, self.journal_one)

        with self.assertRaises(PermissionDenied):
            decorated_func(request, **kwargs)

    def test_proofreader_can_download_file(self):
        func = Mock()
        decorated_func = decorators.proofreader_for_article_required(func)
        kwargs = {'proofing_task_id': self.proofing_task.pk, 'file_id': self.third_file.pk}

        request = self.prepare_request_with_user(self.proofreader, self.journal_one)

        decorated_func(request, **kwargs)
        self.assertTrue(func.called,
                        "proofreader cannot download proofing file...")

    def test_bad_user_cant_download_file(self):
        request = self.prepare_request_with_user(self.regular_user, self.journal_one)
        test = decorators.can_view_file(request, self.regular_user, self.third_file)
        self.assertFalse(test)

    def test_editor_is_author(self):
        func = Mock()
        decorated_func = decorators.editor_is_not_author(func)
        kwargs = {'article_id': self.article_author_is_owner.pk}

        request = self.prepare_request_with_user(self.editor, self.journal_one)
        response = decorated_func(request, **kwargs)
        expected_path = '/review/article/{0}/access_denied/'.format(
                self.article_author_is_owner.pk)
        self.assertTrue(response.url.endswith(expected_path))

    def test_editor_is_not_author(self):
        func = Mock()
        decorated_func = decorators.editor_is_not_author(func)
        kwargs = {'article_id': self.article_in_production.pk}

        request = self.prepare_request_with_user(self.editor, self.journal_one)
        decorated_func(request, **kwargs)
        self.assertTrue(func.called,
                        "editor_is_not_author wrongly blocks editor from content")

    def test_section_editor_can_access_assigned_article(self):
        func = Mock()
        decorated_func = decorators.editor_user_required(func)
        kwargs = {'article_id': self.article_assigned.pk}

        request = self.prepare_request_with_user(self.section_editor, self.journal_one)
        decorated_func(request, **kwargs)

        self.assertTrue(func.called,
                        "editor_user_required wrongly blocks section editors")

    def test_section_editor_cant_access_random_article(self):
        func = Mock()
        decorated_func = decorators.editor_user_required(func)
        kwargs = {'article_id': self.article_author_copyediting.pk}

        request = self.prepare_request_with_user(self.section_editor, self.journal_one)

        with self.assertRaises(PermissionDenied):
            decorated_func(request, **kwargs)

    def test_article_stage_review_required_with_review_article(self):
        func = Mock()
        decorated_func = decorators.article_stage_review_required(func)
        kwargs = {'article_id': self.article_under_review.pk}

        request = self.prepare_request_with_user(self.editor, None)
        decorated_func(request, **kwargs)

        self.assertTrue(
            func.called,
            "article_stage_review_required wrongly blocks article in review"
        )

    def test_article_stage_review_required_with_bad_article(self):
        func = Mock()
        decorated_func = decorators.article_stage_review_required(func)
        kwargs = {'article_id': self.article_author_copyediting.pk}

        request = self.prepare_request_with_user(self.editor, None)

        with self.assertRaises(PermissionDenied):
            decorated_func(request, **kwargs)

    def test_article_stage_review_required_with_no_article(self):
        func = Mock()
        decorated_func = decorators.article_stage_review_required(func)
        kwargs = {}

        request = self.prepare_request_with_user(self.editor, None)

        with self.assertRaises(Http404):
            decorated_func(request, **kwargs)

    def test_production_manager_roles(self):
        func = Mock()
        decorated_func = decorators.production_manager_roles(func)
        kwargs = {}

        fail_request = self.prepare_request_with_user(
            self.proofing_manager,
            self.journal_one,
            self.press,
        )

        with self.assertRaises(PermissionDenied):
            decorated_func(fail_request, **kwargs)

        users_with_permission = [
            self.editor,
            self.section_editor,
            self.production,
        ]

        for user in users_with_permission:
            success_request = self.prepare_request_with_user(
                user,
                self.journal_one,
                self.press,
            )
            decorated_func(success_request, **kwargs)
            self.assertTrue(
                func.called,
                "production_manager_roles wrongly blocks a user.",
            )

    def test_proofing_manager_roles(self):
        func = Mock()
        decorated_func = decorators.proofing_manager_roles(func)
        kwargs = {}

        fail_request = self.prepare_request_with_user(
            self.production,
            self.journal_one,
            self.press,
        )

        with self.assertRaises(PermissionDenied):
            decorated_func(fail_request, **kwargs)

        users_with_permission = [
            self.editor,
            self.section_editor,
            self.proofing_manager,
        ]

        for user in users_with_permission:
            success_request = self.prepare_request_with_user(
                user,
                self.journal_one,
                self.press,
            )
            decorated_func(success_request, **kwargs)
            self.assertTrue(
                func.called,
                "proofing_manager_roles wrongly blocks a user.",
            )

    def test_production_user_or_editor_required_section_editor(self):
        func = Mock()
        decorated_func = decorators.production_user_or_editor_required(func)
        kwargs = {
            'article_id': self.article_in_production.pk,
        }

        success_request = self.prepare_request_with_user(
            self.section_editor,
            self.journal_one,
            self.press,
        )

        decorated_func(success_request, **kwargs)
        self.assertTrue(
            func.called,
            "production_user_or_editor_required wrongly blocks a SE.",
        )

        fail_request = self.prepare_request_with_user(
            self.second_section_editor,
            self.journal_one,
            self.press,
        )

        with self.assertRaises(PermissionDenied):
            decorated_func(fail_request, **kwargs)

    def test_section_editor_production_no_or_bad_article_id(self):
        func = Mock()
        decorated_func = decorators.production_user_or_editor_required(func)
        no_kwargs = {}
        bad_kwargs = {
            'article_id': self.article_unassigned.pk,
        }

        request = self.prepare_request_with_user(
            self.section_editor,
            self.journal_one,
            self.press,
        )

        with self.assertRaises(PermissionDenied):
            decorated_func(request, **no_kwargs)

        with self.assertRaises(PermissionDenied):
            decorated_func(request, **bad_kwargs)

    def test_loading_keyword_page_fail(self):
        func = Mock()
        decorated_func = decorators.keyword_page_enabled(func)

        request = self.prepare_request_with_user(
            self.admin_user,
            self.journal_one,
            self.press,
        )

        self.assertIsInstance(decorated_func(request), HttpResponseRedirect)

    def test_loading_keyword_page_success(self):
        func = Mock()
        decorated_func = decorators.keyword_page_enabled(func)

        setting_handler.save_setting(
            'general', 
            'keyword_list_page', 
            self.journal_one,
            'on',
        )

        request = self.prepare_request_with_user(
            self.admin_user,
            self.journal_one,
            self.press,
        )

        decorated_func(request)

        # Negate any database changes on keepdb input
        setting_handler.save_setting(
            'general', 
            'keyword_list_page', 
            self.journal_one, 
            '',
        )

        self.assertTrue(
            func.called,
            "keyword_page_enabled wrongly blocks this page from rendering.",
        )

    def test_preprint_editor_or_author_required_authorised(self):
        func = Mock()
        decorated_func = decorators.preprint_editor_or_author_required(func)
        kwargs = {'preprint_id': self.preprint.pk}

        request = self.prepare_request_with_user(
            self.editor,
            repository=self.repository,
        )
        decorated_func(request, **kwargs)

        self.assertTrue(
            func.called,
            "preprint_editor_or_author_required wrongly blocks editor from accessing preprints"
        )

    def test_preprint_editor_or_author_required_author(self):
        func = Mock()
        decorated_func = decorators.preprint_editor_or_author_required(func)
        kwargs = {'preprint_id': self.preprint.pk}

        request = self.prepare_request_with_user(
            self.author,
            repository=self.repository,
        )
        decorated_func(request, **kwargs)

        self.assertTrue(
            func.called,
            "preprint_editor_or_author_required wrongly blocks author from accessing preprints"
        )

    def test_preprint_editor_or_author_required_unauthorised(self):
        func = Mock()
        decorated_func = decorators.preprint_editor_or_author_required(func)
        kwargs = {'preprint_id': self.preprint.pk}

        request = self.prepare_request_with_user(
            self.proofreader,
            repository=self.repository,
        )

        with self.assertRaises(PermissionDenied):
            decorated_func(request, **kwargs)

    def test_is_article_preprint_editor_with_subject_editor(self):
        func = Mock()
        decorated_func = decorators.is_article_preprint_editor(func)
        kwargs = {'preprint_id': self.preprint.pk}

        request = self.prepare_request_with_user(
            self.proofing_manager,
            repository=self.repository,
        )
        decorated_func(request, **kwargs)

        self.assertTrue(
            func.called,
            "is_article_preprint_editor wrongly blocks subject editor from accessing preprints"
        )

    def test_is_article_preprint_editor_with_bad_user(self):
        func = Mock()
        decorated_func = decorators.is_article_preprint_editor(func)
        kwargs = {'preprint_id': self.preprint.pk}

        request = self.prepare_request_with_user(
            self.section_editor,
            repository=self.repository,
        )

        with self.assertRaises(PermissionDenied):
            decorated_func(request, **kwargs)

    def test_is_repository_manager(self):
        func = Mock()
        decorated_func = decorators.is_repository_manager(func)
        kwargs = {'preprint_id': self.preprint.pk}

        request = self.prepare_request_with_user(
            self.editor,
            repository=self.repository,
        )
        decorated_func(request, **kwargs)

        self.assertTrue(
            func.called,
            "is_repository_manager wrongly blocks subject editor from accessing preprints"
        )

    def test_is_repository_manager_with_bad_user(self):
        func = Mock()
        decorated_func = decorators.is_repository_manager(func)
        kwargs = {'preprint_id': self.preprint.pk}

        request = self.prepare_request_with_user(
            self.section_editor,
            repository=self.repository,
        )

        with self.assertRaises(PermissionDenied):
            decorated_func(request, **kwargs)

    def test_press_only(self):
        func = Mock()
        decorated_func = decorators.press_only(func)
        kwargs = {}

        request = self.prepare_request_with_user(
            self.editor,
        )
        decorated_func(request, **kwargs)

        self.assertTrue(
            func.called,
            "press_only incorrectly redirects when there is no journal or repo present in request"
        )

    def test_press_only_with_journal(self):
        func = Mock()
        decorated_func = decorators.press_only(func)

        request = self.prepare_request_with_user(None, self.journal_one)

        self.assertIsInstance(decorated_func(request), HttpResponseRedirect)

        # test that the callback was not called
        self.assertFalse(func.called,
                         "press_only decorator doesn't redirect when request.journal is found")

    def test_submission_authorised_with_bad_user(self):
        func = Mock()
        decorated_func = decorators.submission_authorised(func)

        # enable submission authorisation setting
        setting_handler.save_setting(
            setting_group_name='general',
            setting_name='limit_access_to_submission',
            journal=self.journal_one,
            value='On',
        )

        request = self.prepare_request_with_user(
            self.user_with_no_roles,
            journal=self.journal_one,
        )

        # this decorator should redirect us if it fails
        self.assertIsInstance(decorated_func(request), HttpResponseRedirect)

        # test that the callback was not called
        self.assertFalse(
            func.called,
            "submission_authorised decorator doesn't redirect when a user without the author role is found",
        )

    def test_submission_authorised_with_good_user(self):
        func = Mock()
        decorated_func = decorators.submission_authorised(func)

        # enable submission authorisation setting
        setting_handler.save_setting(
            setting_group_name='general',
            setting_name='limit_access_to_submission',
            journal=self.journal_one,
            value='On',
        )

        request = self.prepare_request_with_user(
            self.author,
            journal=self.journal_one,
        )

        decorated_func(request, {})

        # test that the callback was called
        self.assertTrue(
            func.called,
            "submission_authorised decorator doesn't allow access to a user with the author role",
        )

    def test_submission_authorised_with_setting_off(self):
        func = Mock()
        decorated_func = decorators.submission_authorised(func)

        # force disable submission authorisation setting
        setting_handler.save_setting(
            setting_group_name='general',
            setting_name='limit_access_to_submission',
            journal=self.journal_one,
            value='',
        )

        # user user without roles to test that its not blocked
        request = self.prepare_request_with_user(
            self.user_with_no_roles,
            journal=self.journal_one,
        )

        decorated_func(request, {})

        # test that the callback was called
        self.assertTrue(
            func.called,
            "submission_authorised decorator blocks access when the setting is disabled",
        )

    def test_submission_authorised_with_bad_user_repo(self):
        func = Mock()
        decorated_func = decorators.submission_authorised(func)

        # enable submission authorisation setting
        self.repository.limit_access_to_submission = True
        self.repository.save()

        request = self.prepare_request_with_user(
            self.user_with_no_roles,
            repository=self.repository,
        )

        # this decorator should redirect us if it fails
        self.assertIsInstance(decorated_func(request), HttpResponseRedirect)

        # test that the callback was not called
        self.assertFalse(
            func.called,
            "submission_authorised decorator doesn't redirect when a user without the repo author role is found",
        )

    def test_submission_authorised_with_good_user_repo(self):
        func = Mock()
        decorated_func = decorators.submission_authorised(func)

        # enable submission authorisation setting
        self.repository.limit_access_to_submission = True
        self.repository.save()

        role = core_models.Role.objects.get(
            slug='author',
        )
        repo_role = repository_models.RepositoryRole.objects.create(
            user=self.user_with_no_roles,
            repository=self.repository,
            role=role,
        )

        request = self.prepare_request_with_user(
            self.user_with_no_roles,
            repository=self.repository,
        )

        decorated_func(request, {})

        # test that the callback was called
        self.assertTrue(
            func.called,
            "submission_authorised decorator doesn't allow access to a user with the author repo role",
        )

        # Delete the repo role once we're done with it
        repo_role.delete()

    def test_submission_authorised_with_repo_setting_off(self):
        func = Mock()
        decorated_func = decorators.submission_authorised(func)

        # enable submission authorisation setting
        self.repository.limit_access_to_submission = False
        self.repository.save()

        request = self.prepare_request_with_user(
            self.user_with_no_roles,
            repository=self.repository,
        )

        decorated_func(request, {})

        # test that the callback was called
        self.assertTrue(
            func.called,
            "submission_authorised decorator doesn't allow access to a user with the author repo role when off",
        )

    def test_submission_authorised_staff(self):
        func = Mock()
        decorated_func = decorators.submission_authorised(func)

        # enable submission authorisation setting
        self.repository.limit_access_to_submission = True
        self.repository.save()

        request = self.prepare_request_with_user(
            self.staff_member,
            repository=self.repository,
        )

        decorated_func(request, {})

        # test that the callback was called
        self.assertTrue(
            func.called,
            "submission_authorised decorator doesn't allow access to a staff user.",
        )

    def test_submission_authorised_repo_manager(self):
        func = Mock()
        decorated_func = decorators.submission_authorised(func)

        # enable submission authorisation setting
        self.repository.limit_access_to_submission = True
        self.repository.save()

        request = self.prepare_request_with_user(
            self.repo_manager,
            repository=self.repository,
        )

        decorated_func(request, {})

        # test that the callback was called
        self.assertTrue(
            func.called,
            "submission_authorised decorator doesn't allow access to a repo manager.",
        )

    def test_submission_authorised_journal_editor(self):
        func = Mock()
        decorated_func = decorators.submission_authorised(func)

        setting_handler.save_setting(
            setting_group_name='general',
            setting_name='limit_access_to_submission',
            journal=self.journal_one,
            value='',
        )

        # user user without roles to test that its not blocked
        request = self.prepare_request_with_user(
            self.editor,
            journal=self.journal_one,
        )

        decorated_func(request, {})

        # test that the callback was called
        self.assertTrue(
            func.called,
            "submission_authorised decorator doesn't allow access to a journal editor.",
        )

    @override_settings(URL_CONFIG="domain")
    def test_get_author_role(self):
        role = core_models.Role.objects.get(
            slug='author',
        )

        # test the access request form
        form = core_forms.AccessRequestForm(
            journal=self.journal_one,
            user=self.user_with_no_roles,
            role=role,
            data={
                'text': 'Here is my access request.',
            }
        )
        access_request = form.save()

        # test view for approving access
        data = {
            'approve': access_request.pk,
        }
        self.client.force_login(self.staff_member)
        self.client.post(
            reverse('manage_access_requests'),
            data=data,
            SERVER_NAME="journal1.localhost",
        )

        # try to find an author role for this user
        account_role = core_models.AccountRole.objects.filter(
            user=self.user_with_no_roles,
            journal=self.journal_one,
            role=role,
        )
        self.assertTrue(
            account_role.exists(),
            'No account role was created during the post action on the manage_access_requests view',
        )

        # delete the account role once we are done with it
        account_role.delete()

    def test_article_is_not_submitted_complete(self):
        func = Mock()
        decorated_func = decorators.article_is_not_submitted(func)
        kwargs = {
            'article_id': self.article_unassigned.pk
        }

        request = self.prepare_request_with_user(
            self.regular_user,
        )

        with self.assertRaises(Http404):
            decorated_func(request, **kwargs)

    def test_article_is_not_submitted_unsubmitted(self):
        func = Mock()
        decorated_func = decorators.article_is_not_submitted(func)
        kwargs = {
            'article_id': self.article_unsubmitted.pk
        }

        request = self.prepare_request_with_user(
            self.regular_user,
            journal=self.journal_one,
        )

        decorated_func(request, **kwargs)

        # test that the callback was called
        self.assertTrue(
            func.called,
            "article_is_not_submitted incorrectly raises a 404 when article is unsubmitted.",
        )

    # General helper functions

    @staticmethod
    def create_user(username, roles=None, journal=None):
        """
        Creates a user with the specified permissions.
        :return: a user with the specified permissions
        """
        # For consistency, outsourced to newer testing helpers
        return helpers.create_user(
            username,
            roles=roles,
            journal=journal,
        )

    @staticmethod
    def create_roles(roles=None):
        """
        Creates the necessary roles for testing.
        :return: None
        """
        # For consistency, outsourced to newer testing helpers
        helpers.create_roles(roles=roles)

    @staticmethod
    def create_journals():
        """
        Creates a set of dummy journals for testing
        :return: a 2-tuple of two journals
        """
        update_xsl_files()
        update_settings()
        journal_one = journal_models.Journal(code="TST", domain="journal1.localhost")
        journal_one.save()

        journal_two = journal_models.Journal(code="TSA", domain="journal2.localhost")
        journal_two.save()

        return journal_one, journal_two

    @classmethod
    def setUpTestData(self):
        """
        Setup the test environment.
        :return: None
        """
        self.journal_one, self.journal_two = self.create_journals()
        self.create_roles(["editor", "author", "reviewer", "proofreader",
                           "production", "copyeditor", "typesetter",
                           "proofing-manager", "section-editor"])

        self.regular_user = self.create_user("regularuser@martineve.com")
        self.regular_user.is_active = True
        self.regular_user.save()

        self.second_user = self.create_user("seconduser@martineve.com", ["reviewer"], journal=self.journal_one)
        self.second_user.is_active = True
        self.second_user.save()

        self.admin_user = self.create_user("adminuser@martineve.com")
        self.admin_user.is_staff = True
        self.admin_user.is_active = True
        self.admin_user.save()

        self.inactive_user = self.create_user("disableduser@martineve.com", ["editor", "author", "proofreader",
                                                                             "production"], journal=self.journal_one)
        self.inactive_user.is_active = False
        self.inactive_user.save()

        self.editor = self.create_user("editoruser@martineve.com", ["editor"], journal=self.journal_one)
        self.editor.is_active = True
        self.editor.save()

        self.author = self.create_user("authoruser@martineve.com", ["author"], journal=self.journal_one)
        self.author.is_active = True
        self.author.save()

        self.proofreader = self.create_user("proofreader@martineve.com", ["proofreader"], journal=self.journal_one)
        self.proofreader.is_active = True
        self.proofreader.save()

        self.proofreader_two = self.create_user("proofreader2@martineve.com", ["proofreader"], journal=self.journal_one)
        self.proofreader_two.is_active = True
        self.proofreader_two.save()

        self.production = self.create_user("production@martineve.com", ["production"], journal=self.journal_one)
        self.production.is_active = True
        self.production.save()

        self.copyeditor = self.create_user("copyeditor@martineve.com", ["copyeditor"], journal=self.journal_one)
        self.copyeditor.is_active = True
        self.copyeditor.save()

        self.typesetter = self.create_user("typesetter@martineve.com", ["typesetter"], journal=self.journal_one)
        self.typesetter.is_active = True
        self.typesetter.save()

        self.other_typesetter = self.create_user("other_typesetter@martineve.com", ["typesetter"],
                                                 journal=self.journal_one)
        self.other_typesetter.is_active = True
        self.other_typesetter.save()

        self.proofing_manager = self.create_user(
            "proofing_manager@martineve.com",
            ["proofing-manager"],
            journal=self.journal_one
        )
        self.proofing_manager.is_active = True
        self.proofing_manager.save()

        self.other_typesetter.is_active = True
        self.other_typesetter.save()

        self.section_editor = self.create_user("section_editor@martineve.com", ['section-editor'],
                                               journal=self.journal_one)
        self.section_editor.is_active = True
        self.section_editor.save()

        self.second_section_editor = self.create_user(
            "second_section_editor@martineve.com",
            ['section-editor'],
            journal=self.journal_one,
        )
        self.second_section_editor.is_active = True
        self.second_section_editor.save()

        self.second_reviewer = self.create_user("second_reviewer@martineve.com", ['reviewer'],
                                                journal=self.journal_one)
        self.second_reviewer.is_active = True
        self.second_reviewer.save()

        self.user_with_no_roles = self.create_user("no_roles@janeway.systems", [], journal=self.journal_one)
        self.user_with_no_roles.is_active = True
        self.user_with_no_roles.save()

        self.staff_member = self.create_user("staff@janeway.systems", [], journal=self.journal_one)
        self.staff_member.is_active = True
        self.staff_member.is_staff = True
        self.staff_member.save()

        self.repo_manager = self.create_user("repomanager@janeway.systems")
        self.repo_manager.is_active = True
        self.repo_manager.save()

        self.public_file = core_models.File(mime_type="A/FILE",
                                            original_filename="blah.txt",
                                            uuid_filename="UUID.txt",
                                            label="A file that is public",
                                            description="Oh yes, it's a file",
                                            owner=self.regular_user,
                                            is_galley=False,
                                            privacy="public")

        self.public_file.save()

        self.private_file = core_models.File(mime_type="A/FILE",
                                             original_filename="blah.txt",
                                             uuid_filename="UUID.txt",
                                             label="A file that is private",
                                             description="Oh yes, it's a file",
                                             owner=self.regular_user,
                                             is_galley=False,
                                             privacy="owner")

        self.private_file.save()

        self.third_file = core_models.File(mime_type="A/FILE",
                                           original_filename="blah.txt",
                                           uuid_filename="UUID.txt",
                                           label="A file that is private",
                                           description="Oh yes, it's a file",
                                           owner=self.author,
                                           is_galley=False,
                                           privacy="owner")

        self.third_file.save()

        self.article_in_production = submission_models.Article(owner=self.regular_user, title="A Test Article",
                                                               abstract="An abstract",
                                                               stage=submission_models.STAGE_TYPESETTING,
                                                               journal_id=self.journal_one.id)
        self.article_in_production.save()
        self.article_in_production.data_figure_files.add(self.public_file)

        self.article_in_proofing = submission_models.Article(owner=self.regular_user, title="A Test Article",
                                                             abstract="An abstract",
                                                             stage=submission_models.STAGE_PROOFING,
                                                             journal_id=self.journal_one.id)
        self.article_in_proofing.save()
        self.article_in_proofing.data_figure_files.add(self.public_file)

        self.proofing_assigned = production_models.ProductionAssignment(article=self.article_in_proofing,
                                                                        production_manager=self.production)
        self.proofing_assigned.save()

        self.article_unsubmitted = submission_models.Article(owner=self.regular_user, title="A Test Article",
                                                             abstract="An abstract",
                                                             stage=submission_models.STAGE_UNSUBMITTED,
                                                             journal_id=self.journal_one.id)
        self.article_unsubmitted.save()

        self.article_unassigned = submission_models.Article(owner=self.regular_user, title="A Test Article",
                                                            abstract="An abstract",
                                                            stage=submission_models.STAGE_UNASSIGNED,
                                                            journal_id=self.journal_one.id,
                                                            date_submitted=timezone.now())
        self.article_unassigned.save()

        self.article_assigned = submission_models.Article(owner=self.regular_user, title="A Test Article",
                                                          abstract="An abstract",
                                                          stage=submission_models.STAGE_ASSIGNED,
                                                          journal_id=self.journal_one.id)
        self.article_assigned.save()

        self.article_under_review = submission_models.Article(owner=self.regular_user, title="A Test Article",
                                                              abstract="An abstract",
                                                              stage=submission_models.STAGE_UNDER_REVIEW,
                                                              journal_id=self.journal_one.id)
        self.article_under_review.save()

        self.article_review_completed = submission_models.Article.objects.create(owner=self.regular_user,
                                                                                 title="A Test Article",
                                                                                 abstract="An abstract",
                                                                                 stage=submission_models.STAGE_ACCEPTED,
                                                                                 journal_id=self.journal_one.id,
                                                                                 date_accepted=timezone.now())

        self.article_author_is_owner = submission_models.Article.objects.create(owner=self.author,
                                                                                title="A Test Article",
                                                                                abstract="An abstract",
                                                                                stage=submission_models.STAGE_ACCEPTED,
                                                                                journal_id=self.journal_one.id,
                                                                                date_accepted=timezone.now())

        self.article_author_is_owner.authors.add(self.editor)
        self.article_author_is_owner.authors.add(self.author)

        self.review_form = review_models.ReviewForm(name="A Form", slug="A Slug", intro="i", thanks="t",
                                                    journal=self.journal_one)
        self.review_form.save()

        self.review_assignment_complete = review_models.ReviewAssignment(article=self.article_review_completed,
                                                                         reviewer=self.regular_user,
                                                                         editor=self.editor,
                                                                         date_due=datetime.datetime.now(),
                                                                         form=self.review_form,
                                                                         is_complete=True,
                                                                         date_complete=timezone.now())

        self.review_assignment_complete.save()

        self.review_assignment = review_models.ReviewAssignment(article=self.article_under_review,
                                                                reviewer=self.second_user,
                                                                editor=self.editor,
                                                                date_due=datetime.datetime.now(),
                                                                form=self.review_form)

        self.review_assignment.save()

        self.review_assignment_not_in_scope = review_models.ReviewAssignment(article=self.article_in_production,
                                                                             reviewer=self.regular_user,
                                                                             editor=self.editor,
                                                                             date_due=datetime.datetime.now(),
                                                                             form=self.review_form)
        self.review_assignment_not_in_scope.save()

        self.article_under_revision = submission_models.Article(owner=self.regular_user, title="A Test Article",
                                                                abstract="An abstract",
                                                                stage=submission_models.STAGE_UNDER_REVISION,
                                                                journal_id=self.journal_one.id)
        self.article_under_revision.save()

        self.article_rejected = submission_models.Article(owner=self.regular_user, title="A Test Article",
                                                          abstract="An abstract",
                                                          stage=submission_models.STAGE_REJECTED,
                                                          journal_id=self.journal_one.id)
        self.article_rejected.save()

        self.article_accepted = submission_models.Article(owner=self.regular_user, title="A Test Article",
                                                          abstract="An abstract",
                                                          stage=submission_models.STAGE_ACCEPTED,
                                                          journal_id=self.journal_one.id)
        self.article_accepted.save()

        self.section_editor_assignment = review_models.EditorAssignment(article=self.article_assigned,
                                                                        editor=self.section_editor,
                                                                        editor_type='section-editor',
                                                                        notified=True)
        self.section_editor_assignment.save()

        self.production_section_editor_assignment = review_models.EditorAssignment(
            article=self.article_in_production,
            editor=self.section_editor,
            editor_type='section-editor',
            notified=True)
        self.production_section_editor_assignment.save()

        self.article_editor_copyediting = submission_models.Article(owner=self.regular_user, title="A Test Article",
                                                                    abstract="An abstract",
                                                                    stage=submission_models.STAGE_EDITOR_COPYEDITING,
                                                                    journal_id=self.journal_one.id)
        self.article_editor_copyediting.save()

        self.article_author_copyediting = submission_models.Article(owner=self.regular_user, title="A Test Article",
                                                                    abstract="An abstract",
                                                                    stage=submission_models.STAGE_AUTHOR_COPYEDITING,
                                                                    journal_id=self.journal_one.id)
        self.article_author_copyediting.save()

        self.article_final_copyediting = submission_models.Article(owner=self.regular_user, title="A Test Article",
                                                                   abstract="An abstract",
                                                                   stage=submission_models.STAGE_FINAL_COPYEDITING,
                                                                   journal_id=self.journal_one.id)
        self.article_final_copyediting.save()

        self.article_proofing = submission_models.Article(owner=self.regular_user, title="A Test Article",
                                                          abstract="An abstract",
                                                          stage=submission_models.STAGE_PROOFING,
                                                          journal_id=self.journal_one.id)
        self.article_proofing.save()

        self.test_galley = core_models.Galley(
            article=self.article_proofing,
            file=self.third_file,
            label='TXT'
        )
        self.test_galley.save()

        assigned = production_models.ProductionAssignment(article=self.article_in_production,
                                                          production_manager=self.production)
        assigned.save()

        self.article_published = submission_models.Article(owner=self.regular_user, title="A Second Test Article",
                                                           abstract="An abstract",
                                                           stage=submission_models.STAGE_PUBLISHED,
                                                           journal_id=self.journal_one.id)
        self.article_published.save()

        assigned = production_models.ProductionAssignment(article=self.article_published,
                                                          production_manager=self.production)
        assigned.save()

        self.article_in_production_inactive = submission_models.Article(owner=self.regular_user, title="A Test Article",
                                                                        abstract="An abstract",
                                                                        stage=submission_models.STAGE_TYPESETTING,
                                                                        journal_id=self.journal_one.id)
        self.article_in_production_inactive.save()

        self.assigned = production_models.ProductionAssignment(article=self.article_in_production_inactive,
                                                               production_manager=self.inactive_user)
        self.assigned.save()

        self.copyedit_assignment = copyediting_models.CopyeditAssignment(article=self.article_editor_copyediting,
                                                                         editor=self.editor,
                                                                         copyeditor=self.copyeditor,
                                                                         due=timezone.now(),
                                                                         assigned=timezone.now(),
                                                                         notified=True,
                                                                         decision='accepted',
                                                                         date_decided=timezone.now())
        self.copyedit_assignment.save()

        self.typeset_task = production_models.TypesetTask(assignment=self.assigned,
                                                          typesetter=self.typesetter,
                                                          notified=True,
                                                          accepted=timezone.now())
        self.typeset_task.save()

        self.other_typeset_task = production_models.TypesetTask(assignment=self.assigned,
                                                                typesetter=self.other_typesetter,
                                                                notified=True,
                                                                accepted=timezone.now())
        self.other_typeset_task.save()

        self.proofing_assignment = proofing_models.ProofingAssignment(article=self.article_proofing,
                                                                      proofing_manager=self.proofing_manager,
                                                                      notified=True)
        self.proofing_assignment.save()
        self.proofing_assignment.add_new_proofing_round()

        self.proofing_task = proofing_models.ProofingTask(round=self.proofing_assignment.current_proofing_round(),
                                                          proofreader=self.proofreader,
                                                          notified=True,
                                                          due=timezone.now(),
                                                          accepted=timezone.now(),
                                                          task='sdfsdffs')
        self.proofing_task.save()
        self.proofing_task.galleys_for_proofing.add(self.test_galley)

        self.correction_task = proofing_models.TypesetterProofingTask(proofing_task=self.proofing_task,
                                                                      typesetter=self.typesetter,
                                                                      notified=True,
                                                                      due=timezone.now(),
                                                                      accepted=timezone.now(),
                                                                      task='fsddsff')
        self.correction_task.save()

        self.press = press_models.Press.objects.create(name='CTP Press', domain='testserver')

        self.repository, self.repository_subject = helpers.create_repository(
            self.press,
            [self.admin_user, self.editor, self.repo_manager],
            [self.proofing_manager],
        )
        self.preprint = helpers.create_preprint(
            repository=self.repository,
            author=self.author,
            subject=self.repository_subject,
        )

        call_command('load_default_settings')

    @staticmethod
    def mock_messages_add(level, message, extra_tags):
        pass

    @staticmethod
    def get_method(field):
        return None

    @staticmethod
    def prepare_request_with_user(user, journal=None, press=None, repository=None):
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
        request.GET.get = TestSecurity.get_method
        request.journal = journal
        request._messages = Mock()
        request._messages.add = TestSecurity.mock_messages_add
        request.path = '/a/fake/path/'
        request.path_info = '/a/fake/path/'
        request.press = press
        request.repository = repository

        return request
