__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import datetime

from django.test import TestCase, Client
from django.utils import timezone
from django.urls import reverse
from django.core.management import call_command

from utils.tests.setup import create_user, create_journals, create_roles, create_press


class CoreTests(TestCase):
    """
    Regression tests for the core application.
    """

    def setUp(self):
        self.journal_one, self.journal_two = create_journals()
        create_roles(["editor", "author", "reviewer", "proofreader", "production", "copyeditor", "typesetter",
                      "proofing_manager", "section-editor"])

        self.regular_user = create_user("regularuser@martineve.com")
        self.regular_user.is_active = True
        self.regular_user.save()

        self.second_user = create_user("seconduser@martineve.com", ["reviewer"], journal=self.journal_one)
        self.second_user.is_active = True
        self.second_user.save()

        self.admin_user = create_user("adminuser@martineve.com")
        self.admin_user.is_staff = True
        self.admin_user.is_active = True
        self.admin_user.save()

        call_command('sync_settings_to_journals')
        self.journal_one.name = 'Journal One'
        self.journal_two.name = 'Journal Two'
        self.press = create_press()
        self.press.save()
        call_command('sync_journals_to_sites')
