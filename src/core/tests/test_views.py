__copyright__ = "Copyright 2024 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from mock import patch
from uuid import uuid4

from django.test import Client, TestCase, override_settings

from utils.testing import helpers

from core import models as core_models
from core import views as core_views


class CoreViewTestsWithData(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        helpers.create_roles(['author', 'editor', 'reviewer'])
        cls.user_email = 'sukv8golcvwervs0y7e5@example.org'
        cls.user_password = 'xUMXW1oXn2l8L26Kixi2'
        cls.user = core_models.Account.objects.create_user(
            cls.user_email,
            password=cls.user_password,
        )
        cls.user.confirmation_code = uuid4()
        cls.user.is_active = True
        cls.user_orcid = 'https://orcid.org/0000-0001-2345-6789'
        cls.user.orcid = cls.user_orcid
        cls.orcid_token_uuid = uuid4()
        cls.orcid_token = core_models.OrcidToken.objects.create(
            token=cls.orcid_token_uuid,
            orcid=cls.user_orcid,
        )
        cls.reset_token_uuid = uuid4()
        cls.reset_token = core_models.PasswordResetToken.objects.create(
            account=cls.user,
            token=cls.reset_token_uuid,
        )
        cls.user.save()

    def setUp(self):
        self.client = Client()


class GenericFacetedListViewTests(CoreViewTestsWithData):
    """
    A test suite for the core logic in GenericFacetedListView.
    Uses JournalUsers and BaseUserList to get access to URLs and facets
    as they are actually used, and so to help these tests catch
    potential regressions.
    """

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        # Journal 1 users
        cls.journal_one_authors = []
        for num in range(0,30):
            cls.journal_one_authors.append(
                helpers.create_user(
                    f'author_{num}_eblazi52pnxnivl4vox2@example.org',
                    roles=['author'],
                    journal=cls.journal_one,
                )
            )
        cls.journal_one_editor = helpers.create_user(
            'editor_q2flnkp5ryxqtr5iuvvl@example.org',
            roles=['editor'],
            journal=cls.journal_one,
        )
        cls.journal_one_editor.is_active = True
        cls.journal_one_editor.save()
        cls.journal_one_reviewer = cls.journal_one_authors[0]
        cls.journal_one_reviewer.add_account_role('reviewer', cls.journal_one)

        # Journal 2 users
        cls.journal_two_authors = []
        # The first five authors are the same as journal 1
        for author in cls.journal_one_authors[:5]:
            cls.journal_two_authors.append(
                author.add_account_role('author', cls.journal_two)
            )
        # The next five are new
        for num in range(0,5):
            cls.journal_two_authors.append(
                helpers.create_user(
                    f'author_{num}_c9zn2ag7efuyecanpyl1@example.org',
                    roles=['author'],
                    journal=cls.journal_two,
                )
            )
        # Journal 2's reviewer is the same as journal 1's 15th author
        cls.journal_two_reviewer = cls.journal_one_authors[15]
        cls.journal_two_reviewer.add_account_role(
            'reviewer',
            journal=cls.journal_two,
        )

    def setUp(self):
        super().setUp()
        self.client.force_login(self.journal_one_editor)

    def test_get_paginate_by_default(self):
        url = '/user/all/'
        data = {}
        response = self.client.get(url, data)
        self.assertEqual(response.context['paginate_by'], 25)
        self.assertEqual(len(response.context['account_list']), 25)

    def test_get_paginate_by_all(self):
        url = '/user/all/'
        data = {
            'paginate_by': 'all',
        }
        response = self.client.get(url, data)
        self.assertGreater(len(response.context['account_list']), 25)

    def test_get_facet_form_foreign_key(self):
        """
        Checks that only account roles in Journal One
        are included in facet counts.
        """
        url = '/user/all/'
        data = {}
        response = self.client.get(url, data)
        form = response.context['facet_form']
        self.assertEqual(
            form.fields['accountrole__role__pk'].choices,
            [
                (1, 'Author (30)'),
                (2, 'Editor (1)'),
                (3, 'Reviewer (1)'),
            ]
        )

    def test_get_queryset_foreign_key(self):
        """
        Checks that only account roles in Journal One
        are included in queryset results.
        """
        url = '/user/all/'
        data = {
            'accountrole__role__pk': 3, # filter to reviewers
        }
        response = self.client.get(url, data)
        self.assertEqual(len(response.context['account_list']), 1)
