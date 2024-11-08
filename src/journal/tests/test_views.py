__copyright__ = "Copyright 2024 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from django.test import Client, TestCase
from django.utils import timezone

from utils.testing import helpers

class PublishedArticlesListViewTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.sections = []
        cls.articles = []
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        for section_name in ['Article', 'Review', 'Comment', 'Editorial']:
            section = helpers.create_section(
                journal=cls.journal_one,
                name=section_name,
            )
            cls.sections.append(section)
            for num in range(1, 16):
                cls.articles.append(
                    helpers.create_article(
                        journal=cls.journal_one,
                        title=f'{section_name} {num}',
                        section=section,
                        stage='Published',
                        date_published=thirty_days_ago,
                    )
                )

    def setUp(self):
        self.client = Client()

    def test_count_no_filters(self):
        data = {}
        response = self.client.get('/articles/', data)
        self.assertIn(
            f'60 results',
            response.content.decode(),
        )

    def test_count_filtered_on_section(self):
        data = {
            'section__pk': self.sections[0].pk
        }
        response = self.client.get('/articles/', data)
        self.assertIn(
            f'15 results',
            response.content.decode(),
        )

    def test_counts_match_with_filters(self):
        data = {
            'section__pk': self.sections[0].pk,
        }
        response = self.client.get('/articles/', data)
        self.assertIn(
            f'15 results',
            response.content.decode(),
        )
        self.assertIn(
            f'Article (15)',
            response.content.decode(),
        )
