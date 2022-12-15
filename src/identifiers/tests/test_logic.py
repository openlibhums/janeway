import datetime
from io import BytesIO, StringIO
import json
import mock
import pytz
import os


from django.test import TestCase
from django.conf import settings
from django.utils import timezone

from identifiers import logic, models
from core.models import SettingGroup
from journal import logic as journal_logic
from submission import models as submission_models
from utils.testing import helpers
from utils.setting_handler import save_setting
from utils.shared import clear_cache
from lxml import etree
from bs4 import BeautifulSoup
import requests
class TestLogic(TestCase):

    @classmethod
    def setUpTestData(cls):

        # Create press and journals
        cls.press = helpers.create_press()
        cls.press.save()
        cls.journal_one, cls.journal_two = helpers.create_journals()

        # Configure settings
        for journal in [cls.journal_one, cls.journal_two]:
            save_setting('general', 'journal_issn', journal, '1234-5678')
            save_setting('general', 'print_issn', journal, '8765-4321')
            save_setting('Identifiers', 'use_crossref', journal, True)
            save_setting('Identifiers', 'crossref_prefix', journal, '10.0000')
            save_setting('Identifiers', 'crossref_email', journal, 'sample_email@example.com')
            save_setting('Identifiers', 'crossref_name', journal, 'Journal Name')
            save_setting('Identifiers', 'crossref_registrant', journal, 'registrant')

        # Make mock request
        cls.request = helpers.Request()
        cls.request.press = cls.press
        cls.request.journal = cls.journal_one

        # Issue 5.3 has one article
        cls.issue_five_three = helpers.create_issue(cls.journal_one, vol=5, number=3)

        cls.article_one = helpers.create_article(cls.journal_one, with_author=True)
        cls.article_published = helpers.create_article(cls.journal_one, with_author=True)
        cls.article_published.stage = submission_models.STAGE_PUBLISHED
        cls.article_published.date_published = timezone.now()
        cls.article_published.save()

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
        cls.issue_six_one = helpers.create_issue(cls.journal_one, vol=6, number=1)

        cls.article_two = helpers.create_article(cls.journal_one, with_author=True)
        cls.doi_two = logic.generate_crossref_doi_with_pattern(cls.article_two)
        cls.issue_six_one.articles.add(cls.article_two)
        cls.article_two.primary_issue = cls.issue_six_one
        cls.article_two.save()

        cls.article_three = helpers.create_article(cls.journal_one, with_author=True)
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
        cls.article_four = helpers.create_article(cls.journal_one, with_author=True)
        cls.article_four.ISSN_override = '5555-5555'
        cls.doi_four = logic.generate_crossref_doi_with_pattern(cls.article_four)
        cls.issue_six_one.articles.add(cls.article_four)
        cls.article_four.primary_issue = cls.issue_six_one
        cls.article_four.save()

        cls.article_five = helpers.create_article(cls.journal_one, with_author=True)
        cls.article_five.publication_title = 'A Very Special Old Publication'
        cls.doi_five = logic.generate_crossref_doi_with_pattern(cls.article_five)
        cls.issue_six_one.articles.add(cls.article_five)
        cls.article_five.primary_issue = cls.issue_six_one
        cls.article_five.save()

        cls.issue_six_one.save()


        # Journal 2 is a conference
        cls.journal_two.is_conference = True
        cls.issue_nine_nine = helpers.create_issue(cls.journal_two, vol=9, number=9)

        cls.article_six = helpers.create_article(cls.journal_two, with_author=True)
        cls.doi_six = logic.generate_crossref_doi_with_pattern(cls.article_six)
        cls.issue_nine_nine.articles.add(cls.article_six)
        cls.article_six.primary_issue = cls.issue_nine_nine
        cls.article_six.abstract = 'Test abstract.'
        cls.article_six.snapshot_authors()
        cls.article_six.license = submission_models.Licence.objects.filter(
            journal=cls.journal_two,
        ).first()
        cls.article_six.page_numbers = '58-62'
        cls.article_six.save()

        cls.article_seven = helpers.create_article(cls.journal_two, with_author=True)
        cls.doi_seven = logic.generate_crossref_doi_with_pattern(cls.article_seven)
        cls.issue_nine_nine.articles.add(cls.article_seven)
        cls.article_seven.primary_issue = cls.issue_nine_nine
        cls.article_seven.save()

        cls.issue_nine_nine.save()


        # Schema location for Crossref XML validation
        cls.schema_base_path = os.path.join(
            settings.BASE_DIR,
            'identifiers',
            'tests',
            'test_data',
            'schemas',
        )

    def test_create_crossref_doi_batch_context(self):
        self.maxDiff = None
        expected_data = {}

        expected_data['depositor_email'] = 'sample_email@example.com'
        expected_data['depositor_name'] = 'Journal Name'
        expected_data['registrant'] = 'registrant'
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
            'title': 'Journal One',
            'journal_issn': '1234-5678',
            'print_issn': '8765-4321',
            'press': self.journal_one.press
        }
        context = logic.create_crossref_journal_context(self.journal_one)
        self.assertEqual(expected_data, context)


    def test_create_crossref_article_context_published(self):
        self.maxDiff = None
        expected_data = {
            'title': self.article_published.title,
            'abstract': '',
            'url': self.article_published.url,
            'authors': [
                author.email for author in self.article_published.frozenauthor_set.all()
            ],
            'citation_list': None,
            'date_accepted': None,
            'date_published': self.article_published.date_published,
            'doi': f'10.0000/TST.{self.article_published.id}',
            'id': self.article_published.id,
            'license': '',
            'pages': self.article_published.page_numbers,
            'scheduled': True,
        }

        context = logic.create_crossref_article_context(self.article_published)
        context['authors'] = [author.email for author in context['authors']]
        self.assertEqual(expected_data, context)

    def test_create_crossref_article_context_not_published(self):
        expected_data = {
            'title': self.article_one.title,
            'abstract': self.article_one.abstract,
            'url': self.article_one.url,
            'authors': [
                author.email for author in self.article_one.frozenauthor_set.all()
            ],
            'citation_list': None,
            'date_accepted': None,
            'date_published': None,
            'doi': self.doi_one.identifier,
            'id': self.article_one.id,
            'license': submission_models.Licence.objects.filter(
                journal=self.journal_one,
            ).first().url,
            'pages': self.article_one.page_numbers,
            'scheduled': False,
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

        for journal in [self.journal_one, self.journal_two]:
            # Generate batch and validate against schema
            template = 'common/identifiers/crossref_doi_batch.xml'
            identifiers = set([identifier for identifier in models.Identifier.objects.filter(
                article__journal=journal
            )])
            template_context = logic.create_crossref_doi_batch_context(
                journal,
                identifiers,
            )
            deposit = logic.render_to_string(template, template_context)

            soup = BeautifulSoup(deposit, 'lxml')
            version = soup.find('doi_batch')['version']
            schema_filename = f'crossref{version}.xsd'
            with open(os.path.join(self.schema_base_path, schema_filename)) as fileref:
                xml_schema_doc = etree.parse(fileref)
            xml_schema = etree.XMLSchema(xml_schema_doc)

            deposit_bytes = BytesIO(str.encode(deposit))
            doc = etree.parse(deposit_bytes)
            xml_schema.assertValid(doc)
            self.assertTrue(xml_schema.validate(doc))

    def test_journal_deposit_xml_document_has_basically_correct_components(self):
        template = 'common/identifiers/crossref_doi_batch.xml'
        identifiers = set([identifier for identifier in models.Identifier.objects.filter(
            article__journal=self.journal_one
        )])
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

    def test_conference_deposit_xml_document_has_basically_correct_components(self):
        template = 'common/identifiers/crossref_doi_batch.xml'
        identifiers = set([identifier for identifier in models.Identifier.objects.filter(
            article__journal=self.journal_two
        )])
        template_context = logic.create_crossref_doi_batch_context(
            self.journal_two,
            identifiers,
        )
        deposit = logic.render_to_string(template, template_context)
        soup = BeautifulSoup(deposit, 'lxml')
        # There should be one doi_batch
        self.assertEqual(1, len(soup.find_all('doi_batch')))
        # There should be one conference (crossref_issue)
        self.assertEqual(1, len(soup.find_all('conference')))
        # And so conference metadata should appear one time, once for each issue
        self.assertEqual(1, len(soup.find_all('event_metadata')))
        # There should be two conference papers (articles)
        self.assertEqual(2, len(soup.find_all('conference_paper')))

    def test_issue_doi_deposited_correctly(self):
        template = 'common/identifiers/crossref_doi_batch.xml'
        issue = self.article_one.issue
        issue.doi = issue_doi = "10.0001/issue"
        issue.save()
        identifier = self.article_one.get_doi_object
        clear_cache()

        template_context = logic.create_crossref_doi_batch_context(
            self.article_one.journal,
            {identifier},
        )
        deposit = logic.render_to_string(template, template_context)

        soup = BeautifulSoup(deposit, 'lxml')
        # There should be one doi_batch
        issue_soup = soup.find('journal_issue')
        found = False
        if issue_soup:
            issue_doi_soup = issue_soup.find("doi_data")
            if issue_doi_soup:
                self.assertEqual(issue_doi_soup.find("doi").string, issue_doi)
                self.assertEqual(issue_doi_soup.find("resource").string, issue.url)
                found = True
        if not found:
            raise AssertionError("No Issue DOI found on article deposit")

    def test_journal_doi_deposited_correctly(self):
        template = 'common/identifiers/crossref_doi_batch.xml'
        issue = self.article_one.issue
        journal_doi = "10.0001/journal"
        save_setting('Identifiers', 'title_doi', issue.journal, journal_doi)
        identifier = self.article_one.get_doi_object
        clear_cache()

        template_context = logic.create_crossref_doi_batch_context(
            self.article_one.journal,
            {identifier},
        )
        deposit = logic.render_to_string(template, template_context)

        soup = BeautifulSoup(deposit, 'lxml')
        # There should be one doi_batch
        journal_soup = soup.find('journal_metadata')
        found = False
        if journal_soup:
            doi_soup = journal_soup.find("doi_data")
            if doi_soup:
                self.assertEqual(doi_soup.find("doi").string, journal_doi)
                self.assertEqual(
                    doi_soup.find("resource").string, issue.journal.site_url())
                found = True
        if not found:
            raise AssertionError("No Issue DOI found on article deposit")

    def test_issue_doi_auto_assign_enabled(self):
        issue = helpers.create_issue(self.journal_one, vol=99, number=99)
        self.request.POST = {"assign_issue": issue.pk}
        mock_messages = mock.patch('journal.logic.messages').start()
        mock_messages.messages = mock.MagicMock()
        save_setting('Identifiers', 'register_issue_dois', self.journal_one, 'on')
        from events import registration # Forces events to load into memory
        journal_logic.handle_assign_issue(self.request, self.article_one, issue)
        issue.refresh_from_db()
        self.assertTrue(issue.doi)

    def test_issue_doi_auto_assigned_disabled(self):
        issue = helpers.create_issue(self.journal_one, vol=99, number=99)
        self.request.POST = {"assign_issue": issue.pk}
        mock_messages = mock.patch('journal.logic.messages').start()
        mock_messages.messages = mock.MagicMock()
        save_setting('Identifiers', 'register_issue_dois', self.journal_one, '')
        from events import registration # Forces events to load into memory
        journal_logic.handle_assign_issue(self.request, self.article_one, issue)
        issue.refresh_from_db()
        self.assertEqual(issue.doi, None)

    def test_check_crossref_settings(self):

        # Missing settings
        save_setting('Identifiers', 'crossref_prefix', self.journal_one, '')
        save_setting('Identifiers', 'crossref_username', self.journal_one, '')
        save_setting('Identifiers', 'crossref_password', self.journal_one, '')

        use_crossref, test_mode, missing_settings = logic.check_crossref_settings(
            self.journal_one
        )

        # Put need missing setting back
        save_setting('Identifiers', 'crossref_prefix', self.journal_one, '10.0000')

        self.assertEqual(use_crossref, True)
        self.assertEqual(missing_settings, ['crossref_prefix', 'crossref_username', 'crossref_password'])
