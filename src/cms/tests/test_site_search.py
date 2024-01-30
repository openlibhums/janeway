import os

from django.test import TestCase
from django.core.management import call_command
from django.conf import settings

from cms import models as cms_models
from cms import logic as cms_logic
from press import models as press_models
from utils.testing import helpers

from unittest.mock import patch
from bs4 import BeautifulSoup


class TestSiteSearch(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.press = press_models.Press.objects.first()
        if not cls.press:
            cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.docs_label = os.path.join(
            settings.SITE_SEARCH_DIR,
            f'_press_{ cls.press.pk }_documents.json'
        )
        cls.searchable_page = '''
          <!DOCTYPE html>
          <html>
            <head><title>Seasons</title></head>
            <body>
              <div>
                <h2 id="spring">Spring</h2>
                <p>March</p>
                <p>April</p>
                <div id="may">
                  <h3>May</h3>
                  <p>May Day</p>
                </div>
                <div>
                  <div>
                    <h2 id="summer">Summer</h2>
                  </div>
                  <p>June</p>
                  <p>
                    <a href="#thing-on-page">July</a>
                  </p>
                  <h2 id="autumn">Autumn</h2>
                  <p>September</p>
                </div>
              </div>
              <div>
                <h2 id="winter">Winter</h2>
                <p>New Year</p>
              </div>
              <script>Do not index me</script>
            </body>
          </html>
        '''

    @classmethod
    def tearDownClass(cls):
        cls.press.delete()
        cls.journal_one.delete()
        cls.journal_two.delete()

    def setUp(self):
        self.docs = []

    def tearDown(self):
        del self.docs
        try:
            call_command('delete_site_search_data', '--press_id', self.press.pk)
        except FileNotFoundError:
            pass

    def test_add_search_index_document(self):
        docs = cms_logic.add_search_index_document(
            self.docs,
            'example.org',
            'Example',
            'Hello',
        )
        self.assertDictEqual(
            docs[-1],
            {
                'id': 0,
                'url': 'example.org',
                'name': 'Example',
                'text': 'Hello',
            }
        )
        self.assertEqual(len(docs), 1)
        docs = cms_logic.add_search_index_document(
            docs,
            'example.org/2',
            'Other',
            'Hi',
        )
        self.assertEqual(docs[-1]['id'], 1)
        self.assertEqual(len(docs), 2)

    def test_gobble_sibling_text(self):
        soup = BeautifulSoup(self.searchable_page, 'html.parser')
        spring = soup.find(id='spring')
        spring_text = cms_logic.gobble_sibling_text(spring.next_sibling, spring)
        self.assertIn('March', spring_text)
        self.assertNotIn('June', spring_text)
        summer = soup.find(id='summer')
        summer_text = cms_logic.gobble_sibling_text(
            summer.parent.next_sibling,
            summer
        )
        self.assertIn('June', summer_text)
        self.assertNotIn('August', summer_text)

    def test_get_text_for_parent(self):
        soup = BeautifulSoup(self.searchable_page, 'html.parser')
        summer = soup.find(id='summer')
        summer_text = cms_logic.get_text_for_parent(summer.parent, summer)
        self.assertIn('June', summer_text)
        self.assertNotIn('September', summer_text)

    def test_get_text_for_header(self):
        soup = BeautifulSoup(self.searchable_page, 'html.parser')
        spring = soup.find(id='spring')
        spring_text = cms_logic.get_text_for_header(spring)
        self.assertIn('March', spring_text)
        self.assertIn('May Day', spring_text)
        summer = soup.find(id='summer')
        summer_text = cms_logic.get_text_for_header(summer)
        self.assertIn('June', summer_text)

    @patch('cms.logic.add_search_index_document')
    def test_add_part_as_doc(self, add_doc):
        cms_logic.add_part_as_doc(self.docs, 'example.org', '', 'May')
        add_doc.assert_not_called()
        cms_logic.add_part_as_doc(self.docs, 'example.org', 'Spring', '')
        add_doc.assert_not_called()
        cms_logic.add_part_as_doc(self.docs, 'example.org', 'Spring', 'May')
        add_doc.assert_called_with(self.docs, 'example.org', 'Spring', 'May')

    @patch('cms.logic.add_part_as_doc')
    def test_add_searchable_page_parts(self, add_part):
        soup = BeautifulSoup(self.searchable_page, 'html.parser')
        body = soup.find('body')
        self.assertTrue(soup.find(id='winter'))
        docs = cms_logic.add_searchable_page_parts(self.docs, 'example.org', body)
        add_part.assert_called_with(
            docs,
            'example.org#winter',
            'Winter',
            'New Year',
        )
        self.assertFalse(soup.find(id='winter'))

    def test_get_name(self):
        html_with_h1 = BeautifulSoup('<h1>h1</h1>', 'html.parser')
        name = cms_logic.get_name(html_with_h1)
        self.assertEqual(name, 'h1')
        html_with_title = BeautifulSoup('<title>title</title>', 'html.parser')
        name = cms_logic.get_name(html_with_title)
        self.assertEqual(name, 'title')

    def test_get_body(self):
        soup = BeautifulSoup(self.searchable_page, 'html.parser')
        body = cms_logic.get_body(soup)
        self.assertNotIn('Do not index me', body.get_text())

    def test_excluded_urls(self):
        self.assertListEqual(
            [self.journal_one.site_url(), self.journal_two.site_url()],
            cms_logic.excluded_urls()
        )

    @patch('cms.logic.get_base')
    @patch('cms.logic.excluded_urls')
    def test_url_in_scope(self, excluded_urls, get_base):
        get_base.return_value = 'https://www.openlibhums.org'
        excluded_urls.return_value = ['https://www.openlibhums.org/journal1']
        self.assertTrue(
            cms_logic.url_in_scope(
                self.press,
                'https://www.openlibhums.org/my-site-page/',
            ),
        )
        self.assertFalse(
            cms_logic.url_in_scope(
                self.press,
                'https://www.openlibhums.org/journal1/a/',
            )
        )
        self.assertFalse(
            cms_logic.url_in_scope(
                self.press,
                'https://www.wikipedia.org'
            )
        )

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
        cms_logic.update_search_data(self.press)
        docs_file = cms_models.MediaFile.objects.get(label=self.docs_label)
        self.assertTrue(os.path.exists(docs_file.file.path))

    @patch('cms.logic.get_press_site_search_data')
    def test_update_search_data_existing(self, get_press_site_search_data):
        get_press_site_search_data.return_value = [
            {'old': ''}
        ]
        cms_logic.update_search_data(self.press)

        get_press_site_search_data.return_value = [
            {'new': ''}
        ]
        cms_logic.update_search_data(self.press)
        get_press_site_search_data.assert_called()

        media_file = cms_models.MediaFile.objects.get(label=self.docs_label)
        with open(media_file.file.path, 'r') as mf:
            s = mf.read()
            self.assertTrue('old' not in s)
            self.assertTrue('new' in s)
