from django.test import TestCase

from identifiers import logic, models
from core.models import SettingGroup
from submission import models as submission_models
from utils.testing import helpers
from utils.setting_handler import save_setting
from utils.shared import clear_cache
from lxml import etree
from bs4 import BeautifulSoup
import requests
from io import BytesIO, StringIO
import os
import json

class TestLogic(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.press = helpers.create_press()
        cls.press.save()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        save_setting('general', 'journal_issn', cls.journal_one, '1234-5678')
        save_setting('general', 'print_issn', cls.journal_one, '8765-4321')
        save_setting('Identifiers', 'use_crossref', cls.journal_one, True)
        save_setting('Identifiers', 'crossref_prefix', cls.journal_one, '10.0000')
        cls.request = helpers.Request()
        cls.request.press = cls.press
        cls.request.journal = cls.journal_one

        # Issue 5.3 has one article
        cls.issue_five_three = helpers.create_issue(cls.journal_one, volume=5, issue_number=3)

        cls.article_one = helpers.create_article(cls.journal_one)
        cls.doi_one = logic.generate_crossref_doi_with_pattern(cls.article_one)
        cls.issue_five_three.articles.add(cls.article_one)
        cls.article_one.primary_issue = cls.issue_five_three
        cls.article_one.abstract = 'Test abstract.'
        cls.article_one.snapshot_authors()
        cls.article_one.license = submission_models.Licence.objects.filter(
            journal=cls.journal_one,
        ).first()
        cls.article_one.page_numbers = '1-72'
        cls.article_one.save()

        cls.issue_five_three.save()

        # Issue 6.1 has two articles that should be registered together
        # in a single Crossref journal issue block
        cls.issue_six_one = helpers.create_issue(cls.journal_one, volume=6, issue_number=1)

        cls.article_two = helpers.create_article(cls.journal_one)
        cls.doi_two = logic.generate_crossref_doi_with_pattern(cls.article_two)
        cls.issue_six_one.articles.add(cls.article_two)
        cls.article_two.primary_issue = cls.issue_six_one
        cls.article_two.save()

        cls.article_three = helpers.create_article(cls.journal_one)
        doi_options = {
            'id_type': 'doi',
            'identifier': '10.1234/custom',
            'article': cls.article_three,
        }
        cls.doi_three = models.Identifier.objects.create(**doi_options)
        cls.issue_six_one.articles.add(cls.article_three)
        cls.article_three.primary_issue = cls.issue_six_one
        cls.article_three.save()

        # But issue 6.1 also has another couple articles that should be registered individually
        # because they have special attributes
        cls.article_four = helpers.create_article(cls.journal_one)
        cls.article_four.ISSN_override = '5555-5555'
        cls.doi_four = logic.generate_crossref_doi_with_pattern(cls.article_four)
        cls.issue_six_one.articles.add(cls.article_four)
        cls.article_four.primary_issue = cls.issue_six_one
        cls.article_four.save()

        cls.article_five = helpers.create_article(cls.journal_one)
        cls.article_five.publication_title = 'A Very Special Old Publication'
        cls.doi_five = logic.generate_crossref_doi_with_pattern(cls.article_five)
        cls.issue_six_one.articles.add(cls.article_five)
        cls.article_five.primary_issue = cls.issue_six_one
        cls.article_five.save()

        cls.issue_six_one.save()

    def test_create_crossref_doi_batch_context(self):
        self.maxDiff = None
        expected_data = {}

        expected_data['depositor_email'] = 'sample_email@example.com'
        save_setting('Identifiers', 'crossref_email',
                     self.journal_one, 'sample_email@example.com')

        expected_data['depositor_name'] = 'Journal One'
        save_setting('Identifiers', 'crossref_name',
                     self.journal_one, 'Journal One')

        expected_data['registrant'] = 'registrant'
        save_setting('Identifiers', 'crossref_registrant',
                     self.journal_one, 'registrant')

        expected_data['is_conference'] = self.journal_one.is_conference

        context = logic.create_crossref_doi_batch_context(
            self.journal_one,
            set([self.doi_one])
        )

        # A couple things need to be adjusted with context for test to work
        for key in ['batch_id', 'now', 'timestamp', 'timestamp_suffix']:
            context.pop(key)

        # Don't test lower levels of nested context in this test
        expected_data['crossref_issues'] = []
        if 'crossref_issues' in context:
            context['crossref_issues'] = []

        self.assertEqual(expected_data, context)


    def test_create_crossef_issues_context(self):
        # Just expect the right number of crossref_issues
        # each with the right keys
        expected_data = [
            {'journal':None,'issue':None,'articles':None} for x in range(4)
        ]

        identifiers = set()
        identifiers.add(self.doi_one) # Should be on its own in 5.3
        identifiers.add(self.doi_two) # Should go together with below in 6.1
        identifiers.add(self.doi_three) # Should go together with above in 6.1
        identifiers.add(self.doi_four) # Should be on its own due to Article.ISSN_override
        identifiers.add(self.doi_five) # Should be on its own due to Article.publication_title
        context = logic.create_crossref_issues_context(
            self.journal_one,
            identifiers,
        )

        # Knock out the lower levels of data
        for i, crossref_issue in enumerate(context):
            for key in context[i].keys():
                context[i][key] = None

        self.assertEqual(expected_data, context)


    def test_create_crossref_issue_context(self):
        expected_issue = self.issue_five_three
        expected_number_of_articles = 1
        context = logic.create_crossref_issue_context(
            self.journal_one,
            set([self.doi_one]),
            self.issue_five_three,
        )
        self.assertEqual(expected_issue, context['issue'])
        self.assertEqual(expected_number_of_articles, len(context['articles']))

        expected_issue = self.issue_six_one
        expected_number_of_articles = 2
        context = logic.create_crossref_issue_context(
            self.journal_one,
            set([self.doi_two, self.doi_three]),
            self.issue_six_one,
        )
        self.assertEqual(expected_issue, context['issue'])
        self.assertEqual(expected_number_of_articles, len(context['articles']))


    def test_create_crossref_journal_context(self):
        expected_data = {
            'journal_title': 'Journal One',
            'journal_issn': '1234-5678',
            'print_issn': '8765-4321',
        }
        context = logic.create_crossref_journal_context(self.journal_one)
        self.assertEqual(expected_data, context)


    def test_create_crossref_article_context(self):
        expected_data = {
            'article_title': self.article_one.title,
            'abstract': self.article_one.abstract,
            'article_url': self.article_one.url,
            'authors': [
                author.email for author in self.article_one.frozenauthor_set.all()
            ],
            'citation_list': None,
            'date_accepted': None,
            'date_published': None,
            'doi': self.doi_one.identifier,
            'license': submission_models.Licence.objects.filter(
                journal=self.journal_one,
            ).first().url,
            'pages': self.article_one.page_numbers
        }

        context = logic.create_crossref_article_context(self.article_one)
        context['authors'] = [author.email for author in context['authors']]

        self.assertEqual(expected_data, context)

    def test_preview_registration_information_when_use_crossref_on(self):
        clear_cache()
        save_setting('Identifiers', 'use_crossref', self.journal_one, True)
        self.assertTrue('Current metadata to send to Crossref' in self.article_one.registration_preview)

    def test_preview_registration_information_when_use_crossref_off(self):
        clear_cache()
        save_setting('Identifiers', 'use_crossref', self.journal_one, False)
        self.assertFalse(self.article_one.registration_preview)

    def test_preview_registration_information_when_custom_doi(self):
        clear_cache()
        self.assertTrue(self.doi_three.identifier in self.article_three.registration_preview)

    def test_deposit_xml_document_is_valid(self):
        self.maxDiff = None

        template = 'common/identifiers/crossref_doi_batch.xml'
        identifiers = set([identifier for identifier in models.Identifier.objects.all()])
        template_context = logic.create_crossref_doi_batch_context(
            self.journal_one,
            identifiers,
        )

        test_run_dir = os.getcwd()
        test_data_path = os.path.join(
            test_run_dir,
            'src',
            'identifiers',
            'tests',
            'test_data',
            'schemas',
            'xml.xsd',
        )
        os.chdir(os.path.dirname(test_data_path))

        # Load deposit document into etree
        deposit = logic.render_to_string(template, template_context)
        deposit_bytes = BytesIO(str.encode(deposit))
        root = etree.parse(deposit_bytes).getroot()

        # Get filename for Crossref schema version declared
        xsd_predicate = '{http://www.w3.org/2001/XMLSchema-instance}schemaLocation'
        xsd_object = root.get(xsd_predicate)
        schema_file_name = xsd_object.split('/')[-1]

        # Open and load corresponding locally saved schema file
        # with open(schema_file_name, 'r') as fileref:
        schema_root = etree.parse(schema_file_name).getroot()
        schema = etree.XMLSchema(schema_root)
        parser = etree.XMLParser(schema=schema)
        deposit_root = etree.fromstring(deposit, parser)
        from nose.tools import set_trace; set_trace()
        os.chdir(test_run_dir)

        # Validate the deposit document
        self.assertTrue(xml_schema.validate(root))


    def test_deposit_xml_document_has_basically_correct_components(self):
        template = 'common/identifiers/crossref_doi_batch.xml'
        identifiers = set([identifier for identifier in models.Identifier.objects.all()])
        template_context = logic.create_crossref_doi_batch_context(
            self.journal_one,
            identifiers,
        )
        deposit = logic.render_to_string(template, template_context)
        soup = BeautifulSoup(deposit, 'lxml')
        # There should be one doi_batch
        self.assertEqual(1, len(soup.find_all('doi_batch')))
        # There should be four crossref_issues
        self.assertEqual(4, len(soup.find_all('journal_issue')))
        # And so journal metadata should appear four times, once for each issue
        self.assertEqual(4, len(soup.find_all('journal_metadata')))
        # There should be five articles
        self.assertEqual(5, len(soup.find_all('journal_article')))

    def test_send_crossref_deposit(self):
        identifiers = set([identifier for identifier in models.Identifier.objects.all()])
        test_mode = True
        status, error = logic.send_crossref_deposit(test_mode, identifiers)
        pass

