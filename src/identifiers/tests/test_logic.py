from django.test import TestCase

from identifiers import logic, models
from core.models import SettingGroup
from submission import models as submission_models
from utils.testing import helpers
from utils.setting_handler import save_setting
from utils.shared import clear_cache


class TestLogic(TestCase):
    def setUp(self):
        self.press = helpers.create_press()
        self.press.save()
        self.journal_one, self.journal_two = helpers.create_journals()
        self.request = helpers.Request()
        self.request.press = self.press
        self.request.journal = self.journal_one
        self.article_one = helpers.create_article(self.journal_one)

    def test_create_crossref_context(self):
        self.maxDiff = None
        expected_data = {}

        self.article_one.abstract = 'Test abstract.'
        expected_data['abstract'] = self.article_one.abstract

        expected_data['article_title'] = 'Test Article from Utils Testing Helpers'

        expected_data['article_url'] = self.article_one.url

        self.article_one.snapshot_authors()
        expected_data['authors'] = [author.email for author in self.article_one.frozenauthor_set.all()]

        save_setting(
            'Identifiers', 'crossref_prefix', self.journal_one, '10.0000')

        expected_data['citation_list'] = None
        expected_data['date_accepted'] = None
        expected_data['date_published'] = None

        save_setting(
            'Identifiers', 'crossref_email', self.journal_one, 'sample_email@example.com')
        expected_data['depositor_email'] = 'sample_email@example.com'

        save_setting(
            'Identifiers', 'crossref_name', self.journal_one, 'Journal One')
        expected_data['depositor_name'] = 'Journal One'

        expected_data['doi'] = self.article_one.render_sample_doi()

        self.issue_five_three = helpers.create_issue(self.journal_one)
        self.issue_five_three.articles.add(self.article_one)
        expected_data['issue'] = self.issue_five_three
        expected_data['journal_issn'] = '0000-0000'
        expected_data['journal_title'] = 'Journal One'

        self.article_one.license = submission_models.Licence.objects.filter(
            journal=self.journal_one,
        ).first()
        expected_data['license'] = submission_models.Licence.objects.filter(
            journal=self.journal_one,
        ).first().url

        self.article_one.page_numbers = '1-72'
        expected_data['pages'] = self.article_one.page_numbers

        expected_data['print_issn'] = ''

        save_setting(
            'Identifiers', 'crossref_registrant', self.journal_one, 'registrant')
        expected_data['registrant'] = 'registrant'


        context = logic.create_crossref_context(self.article_one)

        # A couple things need to be adjusted with context for test to work
        context['authors'] = [author.email for author in context['authors']]
        for k in ['batch_id', 'now', 'timestamp', 'timestamp_suffix']:
            context.pop(k)

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
        save_setting('Identifiers', 'use_crossref', self.journal_one, True)
        doi_options = {
            'id_type': 'doi',
            'identifier': 'https://doi.org/10.1234/custom',
            'article': self.article_one,
        }
        doi = models.Identifier.objects.create(**doi_options)
        self.assertTrue(doi_options['identifier'] in self.article_one.registration_preview)
