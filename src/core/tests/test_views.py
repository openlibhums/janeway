__copyright__ = "Copyright 2024 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from mock import patch
from uuid import uuid4

from django.test import Client, TestCase, override_settings

from utils.testing import helpers

from core import models as core_models


class CoreViewTestsWithData(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        helpers.create_roles(['author'])
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


class AccountManagementTemplateTests(CoreViewTestsWithData):

    def test_user_login(self):
        url = '/login/'
        data = {}
        template = 'admin/core/accounts/login.html'
        response = self.client.get(url, data)
        self.assertTemplateUsed(response, template)

    def test_get_reset_token(self):
        url = '/reset/step/1/'
        data = {}
        template = 'admin/core/accounts/get_reset_token.html'
        response = self.client.get(url, data)
        self.assertTemplateUsed(response, template)

    def test_reset_password(self):
        url = f'/reset/step/2/{self.reset_token_uuid}/'
        data = {}
        template = 'admin/core/accounts/reset_password.html'
        response = self.client.get(url, data)
        self.assertTemplateUsed(response, template)

    def test_register(self):
        url = '/register/step/1/'
        data = {}
        template = 'admin/core/accounts/register.html'
        response = self.client.get(url, data)
        self.assertTemplateUsed(response, template)

    def test_orcid_registration(self):
        url = f'/register/step/orcid/{self.orcid_token_uuid}/'
        data = {}
        template = 'admin/core/accounts/orcid_registration.html'
        response = self.client.get(url, data)
        self.assertTemplateUsed(response, template)

    def test_activate_account(self):
        url = f'/register/step/2/{self.user.confirmation_code}/'
        data = {}
        template = 'admin/core/accounts/activate_account.html'
        response = self.client.get(url, data)
        self.assertTemplateUsed(response, template)

    def test_edit_profile(self):
        self.client.login(username=self.user_email, password=self.user_password)
        url = '/profile/'
        data = {}
        template = 'admin/core/accounts/edit_profile.html'
        response = self.client.get(url, data)
        self.assertTemplateUsed(response, template)
