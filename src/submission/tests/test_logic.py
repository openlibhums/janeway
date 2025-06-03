__copyright__ = "Copyright 2025 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from django.shortcuts import reverse
from django.test import TestCase, client
from mock import patch

from utils.testing import helpers


class TestSubmitAuthorsLogic(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.kathleen = helpers.create_user(
            'haogjlbdmax7b6tnc6qa@example.org',
            roles=['author'],
            journal=cls.journal_one,
            first_name='Kathleen',
            last_name='Booth',
            is_active=True,
        )
        cls.eliot = helpers.create_user(
            'soqdbzkiz7movjtix6hr@example.org',
            roles=['author'],
            journal=cls.journal_one,
            first_name='T.',
            middle_name='S.',
            last_name='Eliot',
            orcid='0000-1234-1234-1234',
        )
        cls.article = helpers.create_article(
            cls.journal_one,
            owner=cls.kathleen,
            current_step=2,
        )
        cls.kathleen_author = cls.kathleen.snapshot_self(cls.article)


    def test_save_author_order_single_author(self):
        self.client.force_login(self.kathleen)
        post_data = {
            'change_order': 'bottom',
            'author_pk': self.kathleen_author.pk,
        }
        response = self.client.post(
            reverse('submit_authors', kwargs={'article_id': self.article.pk}),
            post_data,
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(
            self.kathleen_author.order,
            0,
        )

    def test_save_author_order_three_authors(self):
        # Set up a second and third author
        eliot_author = self.eliot.snapshot_self(self.article)
        eric = helpers.create_user(
            '6cfka43pltcafyzlluxa@example.org',
            roles=['author'],
            journal=self.journal_one,
            first_name='Eric',
            last_name='Hobsbawm',
        )
        eric_author = eric.snapshot_self(self.article)

        # Run test
        self.client.force_login(self.kathleen)
        post_data = {
            'change_order': 'up',
            'author_pk': eliot_author.pk,
        }
        response = self.client.post(
            reverse('submit_authors', kwargs={'article_id': self.article.pk}),
            post_data,
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(
            self.article.frozenauthor_set.first(),
            eliot_author,
        )
        post_data = {
            'change_order': 'down',
            'author_pk': eliot_author.pk,
        }
        self.client.post(
            reverse('submit_authors', kwargs={'article_id': self.article.pk}),
            post_data,
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(
            self.article.frozenauthor_set.first(),
            self.kathleen.frozen_author(self.article),
        )
        post_data = {
            'change_order': 'top',
            'author_pk': eric_author.pk,
        }
        self.client.post(
            reverse('submit_authors', kwargs={'article_id': self.article.pk}),
            post_data,
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(
            self.article.frozenauthor_set.first(),
            eric_author,
        )

    def test_add_author_from_search_orcid_in_janeway(self):
        self.client.force_login(self.kathleen)
        post_data = {
            'search_authors': '',
            'author_search_text': self.eliot.orcid,
        }
        self.client.post(
            reverse('submit_authors', kwargs={'article_id': self.article.pk}),
            post_data,
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertIn(
            self.eliot,
            self.article.author_accounts.all(),
        )

    @patch('utils.orcid.get_orcid_record_details')
    def test_add_author_from_search_orcid_public(self, get_orcid_details):
        eric = helpers.create_user(
            '6cfka43pltcafyzlluxa@example.org',
            roles=['author'],
            journal=self.journal_one,
            first_name='Eric',
            last_name='Hobsbawm',
        )
        get_orcid_details.return_value = {'emails': [eric.email]}
        self.client.force_login(self.kathleen)
        post_data = {
            'search_authors': '',
            'author_search_text': '0000-5678-5678-5678',
        }
        self.client.post(
            reverse('submit_authors', kwargs={'article_id': self.article.pk}),
            post_data,
            SERVER_NAME=self.journal_one.domain,
        )
        eric.refresh_from_db()
        self.assertEqual(eric.orcid, '0000-5678-5678-5678')
        self.assertIn(
            eric,
            self.article.author_accounts.all(),
        )

    @patch('utils.orcid.get_orcid_record_details')
    def test_add_author_from_search_orcid_public_new(self, get_orcid_details):
        get_orcid_details.return_value = {
            'emails': ['6cfka43pltcafyzlluxa@example.org'],
            'first_name': 'Eric',
            'last_name': 'Hobsbawm',
        }
        self.client.force_login(self.kathleen)
        post_data = {
            'search_authors': '',
            'author_search_text': '0000-5678-5678-5678',
        }
        self.client.post(
            reverse('submit_authors', kwargs={'article_id': self.article.pk}),
            post_data,
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(
            self.article.frozenauthor_set.last().email,
            '6cfka43pltcafyzlluxa@example.org',
        )
        self.assertEqual(
            self.article.frozenauthor_set.last().orcid,
            '0000-5678-5678-5678',
        )

    @patch('utils.orcid.get_orcid_record_details')
    def test_add_author_from_search_orcid_public_affiliations(self, get_orcid_details):
        get_orcid_details.return_value = {
            'emails': ['6cfka43pltcafyzlluxa@example.org'],
            'first_name': 'Eric',
            'last_name': 'Hobsbawm',
            'affiliations': [
                {
                    'organization': {
                        'name': 'Birkbeck',
                    }
                }
            ],
        }
        self.client.force_login(self.kathleen)
        post_data = {
            'search_authors': '',
            'author_search_text': '0000-5678-5678-5678',
        }
        self.client.post(
            reverse('submit_authors', kwargs={'article_id': self.article.pk}),
            post_data,
            SERVER_NAME=self.journal_one.domain,
        )
        last_author = self.article.frozenauthor_set.last()
        self.assertEqual(
            last_author.primary_affiliation().__str__(),
            'Birkbeck',
        )
