import os

from django.test import TestCase
from django.core.management import call_command
from django.contrib.contenttypes.models import ContentType
from django.conf import settings

from cms import models as cms_models
from cms import logic as cms_logic
from press import models as press_models
from utils.testing import helpers

from unittest.mock import patch


class TestSiteSearch(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.press = press_models.Press.objects.first()
        if not cls.press:
            cls.press = helpers.create_press()
        content_type = ContentType.objects.get_for_model(cls.press)
        cls.press_contact = helpers.create_contact(content_type, cls.press.pk)
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.docs_label = os.path.join(
            settings.SITE_SEARCH_DIR,
            f'_press_{ cls.press.pk }_documents.json'
        )
        cls.news_item = helpers.create_news_item(content_type, cls.press.pk)
        cls.cms_page = helpers.create_cms_page(content_type, cls.press.pk)

    @classmethod
    def tearDownClass(cls):
        cls.press.delete()
        cls.press_contact.delete()
        cls.journal_one.delete()
        cls.journal_two.delete()
        cls.news_item.delete()
        cls.cms_page.delete()

    def tearDown(self):
        try:
            call_command('delete_site_search_data', '--press_id', self.press.pk)
        except FileNotFoundError:
            pass

    @patch('cms.logic.update_search_data')
    def test_generate_command(self, update_search_data):
        update_search_data.return_value = []
        call_command('generate_site_search_data', '--press_id', self.press.pk)
        update_search_data.assert_called()

    def test_delete_command(self):
        docs_path = os.path.join(
            settings.MEDIA_ROOT,
            'press',
            self.docs_label,
        )
        call_command('generate_site_search_data', '--press_id', self.press.pk)
        self.assertTrue(os.path.exists(docs_path))
        call_command('delete_site_search_data', '--press_id', self.press.pk)
        self.assertFalse(os.path.exists(docs_path))
        self.assertFalse(os.path.exists(cms_logic.SITE_SEARCH_PATH))

    @patch('cms.logic.get_press_site_search_data')
    def test_update_search_data_new(self, get_press_site_search_data):
        get_press_site_search_data.return_value = [
            {'test': 'test value', 'other': 'other value'}
        ]
        cms_logic.update_search_data(self.press.pk)
        docs_file = cms_models.MediaFile.objects.get(label=self.docs_label)
        self.assertTrue(os.path.exists(docs_file.file.path))

    @patch('cms.logic.get_press_site_search_data')
    def test_update_search_data_existing(self, get_press_site_search_data):
        get_press_site_search_data.return_value = [
            {'old': ''}
        ]
        cms_logic.update_search_data(self.press.pk)

        get_press_site_search_data.return_value = [
            {'new': ''}
        ]
        cms_logic.update_search_data(self.press.pk)
        get_press_site_search_data.assert_called()

        media_file = cms_models.MediaFile.objects.get(label=self.docs_label)
        with open(media_file.file.path, 'r') as mf:
            s = mf.read()
            self.assertTrue('old' not in s)
            self.assertTrue('new' in s)
