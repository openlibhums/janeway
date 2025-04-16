__copyright__ = "Copyright 2025 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from django.test import TestCase, client
from mock import patch

from submission import logic
from utils import setting_handler
from utils.testing import helpers


class TestSubmitStartLogic(TestCase):

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
        )
        cls.article = helpers.create_article(cls.journal_one)

    def test_add_user_as_author(self):
        setting_handler.save_setting(
            'general',
            'limit_access_to_submission',
            self.journal_one,
            '',
        )
        logic.add_user_as_author(self.kathleen, self.article)
        self.assertIn(self.kathleen, self.article.authors.all())
        self.assertTrue(self.article.articleauthororder_set.exists())
        self.assertEqual(self.article.correspondence_author, self.kathleen)


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
        logic.add_user_as_author(cls.kathleen, cls.article)


    def test_save_author_order(self):
        # Set up a second and third author
        logic.add_user_as_author(self.eliot, self.article)
        eric = helpers.create_user(
            '6cfka43pltcafyzlluxa@example.org',
            roles=['author'],
            journal=self.journal_one,
            first_name='Eric',
            last_name='Hobsbawm',
        )
        logic.add_user_as_author(eric, self.article)

        # Run test
        self.client.force_login(self.kathleen)
        post_data = {
            'change_order': 'up',
            'author_pk': self.eliot.pk,
        }
        response = self.client.post(
            f'/submit/{self.article.pk}/authors/',
            post_data,
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(
            self.article.articleauthororder_set.first().author,
            self.eliot,
        )
        post_data = {
            'change_order': 'down',
            'author_pk': self.eliot.pk,
        }
        self.client.post(
            f'/submit/{self.article.pk}/authors/',
            post_data,
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(
            self.article.articleauthororder_set.first().author,
            self.kathleen,
        )
        post_data = {
            'change_order': 'first',
            'author_pk': eric.pk,
        }
        self.client.post(
            f'/submit/{self.article.pk}/authors/',
            post_data,
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(
            self.article.articleauthororder_set.first().author,
            eric,
        )

    def test_add_author_from_search_orcid_in_janeway(self):
        self.client.force_login(self.kathleen)
        post_data = {
            'search_authors': '',
            'author_search_text': self.eliot.orcid,
        }
        self.client.post(
            f'/submit/{self.article.pk}/authors/',
            post_data,
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertIn(
            self.eliot,
            self.article.authors.all(),
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
            f'/submit/{self.article.pk}/authors/',
            post_data,
            SERVER_NAME=self.journal_one.domain,
        )
        eric.refresh_from_db()
        self.assertEqual(eric.orcid, '0000-5678-5678-5678')
        self.assertIn(
            eric,
            self.article.authors.all(),
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
            f'/submit/{self.article.pk}/authors/',
            post_data,
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertTrue(
            self.article.articleauthororder_set.last().author.email,
            '6cfka43pltcafyzlluxa@example.org',
        )
        self.assertTrue(
            self.article.articleauthororder_set.last().author.orcid,
            '0000-5678-5678-5678',
        )

    @patch('utils.orcid.get_orcid_record_details')
    def test_add_author_from_search_orcid_public_new(self, get_orcid_details):
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
            f'/submit/{self.article.pk}/authors/',
            post_data,
            SERVER_NAME=self.journal_one.domain,
        )
        last_author = self.article.articleauthororder_set.last().author
        self.assertTrue(
            last_author.primary_affiliation().__str__(),
            'Birkbeck',
        )
