import os

from django.test import TestCase
from django.core.management import call_command
from django.contrib.contenttypes.models import ContentType

from cms import models as cms_models
from cms import logic as cms_logic
from utils.testing import helpers

from unittest.mock import patch
from lunr import lunr
from lunr.index import Index
import json


class TestSiteSearch(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        content_type = ContentType.objects.get_for_model(cls.press)
        cls.press_contact = helpers.create_contact(content_type, cls.press.pk)
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.docs_label = f'_press_{ cls.press.pk }_site_search_documents.json'
        cls.index_label = f'_press_{ cls.press.pk }_site_search_index.json'
        cls.news_item = helpers.create_news_item(content_type, cls.press.pk)
        cls.cms_page = helpers.create_cms_page(content_type, cls.press.pk)

    def tearDown(self):
        for label in [self.docs_label, self.index_label]:
            try:
                media_file = cms_models.MediaFile.objects.get(label=label)
                media_file.unlink()
            except cms_models.MediaFile.DoesNotExist:
                pass

    @patch('cms.logic.update_index')
    def test_generate_command(self, update_index):
        update_index.return_value = ('', '')
        call_command('generate_site_search_index')
        update_index.assert_called()

    @patch('cms.logic.build_index')
    def test_update_index_new(self, build_index):
        build_index.return_value = (
            [{'test': 'test value', 'other': 'other value'}],
            lunr(
                ref='test',
                fields=('test', 'other'),
                documents=[{'test': 'test value', 'other': 'other value'}],
            )
        )
        cms_logic.update_index()
        build_index.assert_called()
        docs_file = cms_models.MediaFile.objects.get(label=self.docs_label)
        self.assertTrue(os.path.exists(docs_file.file.path))
        index_file = cms_models.MediaFile.objects.get(label=self.index_label)
        self.assertTrue(os.path.exists(index_file.file.path))

    @patch('cms.logic.build_index')
    def test_update_index_existing(self, build_index):
        old_docs = [{'old': ''}]
        build_index.return_value = (
            old_docs,
            lunr(
                ref='old',
                fields=('old',),
                documents=old_docs,
            )
        )
        cms_logic.update_index()

        new_docs = [{'new': ''}]
        build_index.return_value = (
            new_docs,
            lunr(
                ref='new',
                fields=('new',),
                documents=new_docs,
            )
        )
        cms_logic.update_index()

        build_index.assert_called()

        for label in [self.docs_label, self.index_label]:
            media_file = cms_models.MediaFile.objects.get(label=label)
            with open(media_file.file.path, 'r') as mf:
                s = mf.read()
                self.assertTrue('old' not in s)
                self.assertTrue('new' in s)

    @patch('cms.logic.get_press_site_search_data')
    def test_build_index(self, get_press_site_search_data):
        get_press_site_search_data.return_value = [{
            'url': '',
            'name': '',
            'people': '',
            'text': '',
            'tags': '',
        }]
        docs, idx = cms_logic.build_index()
        get_press_site_search_data.assert_called()
        self.assertTrue(isinstance(idx, Index))

    def test_get_press_site_search_data(self):
        documents = cms_logic.get_press_site_search_data()
        names = [doc['name'] for doc in documents]
        self.assertTrue(self.cms_page.display_name in names)
        self.assertTrue(self.news_item.title in names)
        self.assertTrue(self.journal_one.name in names)

        text = ''.join([doc['text'] for doc in documents])
        self.assertTrue(self.press_contact.name in text)

    def test_run_search(self):
        call_command('generate_site_search_index')
        media_file = cms_models.MediaFile.objects.get(label=self.index_label)
        with open(media_file.file.path) as fd:
            serialized_idx = json.loads(fd.read())
            idx = Index.load(serialized_idx)
            result = idx.search(self.news_item.title)
            self.assertGreaterEqual(len(result), 1)
