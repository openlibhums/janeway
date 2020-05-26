__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import datetime

from django.test import TestCase, override_settings
from django.urls import reverse
from django.core.management import call_command

from utils.testing import helpers
from core import models


class CoreTests(TestCase):
    """
    Regression tests for the core application.
    """

    @override_settings(URL_CONFIG="domain")
    def test_create_user_form(self):

        data = {
            'email': 'test@test.com',
            'is_active': True,
            'password_1': 'this_is_a_password',
            'password_2': 'this_is_a_password',
            'salutation': 'Prof.',
            'first_name': 'Martin',
            'last_name': 'Eve',
            'department': 'English & Humanities',
            'institution': 'Birkbeck, University of London',
            'country': 235,
        }

        self.client.force_login(self.admin_user)
        response = self.client.post(reverse('core_add_user'), data)

        try:
            models.Account.objects.get(email='test@test.com')
        except models.Account.DoesNotExist:
            self.fail('User account has not been saved.')

    @override_settings(URL_CONFIG="domain")
    def test_create_user_form_normalise_email(self):

        data = {
            'email': 'Test@TEST.com',
            'is_active': True,
            'password_1': 'this_is_a_password',
            'password_2': 'this_is_a_password',
            'salutation': 'Prof.',
            'first_name': 'Martin',
            'last_name': 'Eve',
            'department': 'English & Humanities',
            'institution': 'Birkbeck, University of London',
            'country': 235,
        }

        self.client.force_login(self.admin_user)
        response = self.client.post(reverse('core_add_user'), data)

        try:
            models.Account.objects.get(email='Test@test.com')
        except models.Account.DoesNotExist:
            self.fail('User account has not been saved.')

    def setUp(self):
        self.press = helpers.create_press()
        self.press.save()
        self.journal_one, self.journal_two = helpers.create_journals()
        helpers.create_roles(["editor", "author", "reviewer", "proofreader", "production", "copyeditor", "typesetter",
                            "proofing_manager", "section-editor"])

        self.regular_user = helpers.create_user("regularuser@martineve.com")
        self.regular_user.is_active = True
        self.regular_user.save()

        self.second_user = helpers.create_user("seconduser@martineve.com", ["reviewer"], journal=self.journal_one)
        self.second_user.is_active = True
        self.second_user.save()

        self.admin_user = helpers.create_user("adminuser@martineve.com")
        self.admin_user.is_staff = True
        self.admin_user.is_active = True
        self.admin_user.save()

        self.journal_one.name = 'Journal One'
        self.journal_two.name = 'Journal Two'
        call_command('install_plugins')
