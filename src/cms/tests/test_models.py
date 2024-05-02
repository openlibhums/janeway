__copyright__ = "Copyright 2024 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from unittest.mock import Mock

from django.test import TestCase
from django.contrib.contenttypes.models import ContentType
from django.http import HttpRequest

from press import models as press_models
from journal import models as journal_models
from utils import setting_handler
from utils.testing import helpers


class TestCaseWithCMSData(TestCase):
    """
    This base test case can house data to be used for all CMS app tests
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.press = press_models.Press(domain="cms.example.org")
        cls.press.save()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        press_type = ContentType.objects.get_for_model(cls.press)
        cls.press_cms_page = helpers.create_cms_page(press_type, cls.press.pk)
        journal_type = ContentType.objects.get_for_model(cls.journal_one)
        cls.journal_cms_page = helpers.create_cms_page(journal_type, cls.journal_one.pk)
        setting_handler.save_setting('general', 'custom_cms_templates', None, 'custom')

    @classmethod
    def tearDownClass(cls):
        cls.journal_cms_page.delete()
        cls.press_cms_page.delete()
        cls.journal_one.delete()
        cls.journal_two.delete()
        cls.press.delete()
        super().tearDownClass()

    def setUp(self):
        self.request_journal = Mock(HttpRequest)
        type(self.request_journal).GET = {}
        type(self.request_journal).POST = {}
        type(self.request_journal).journal = Mock(journal_models.Journal)
        type(self.request_journal).press = Mock(press_models.Press)
        journal_type = ContentType.objects.get_for_model(self.journal_one)
        type(self.request_journal).model_content_type = journal_type
        type(self.request_journal).site_type = self.journal_one

        self.request_press = Mock(HttpRequest)
        type(self.request_press).GET = {}
        type(self.request_press).POST = {}
        type(self.request_press).journal = None
        type(self.request_press).press = Mock(press_models.Press)
        press_type = ContentType.objects.get_for_model(self.press)
        type(self.request_press).model_content_type = press_type
        type(self.request_press).site_type = self.press
