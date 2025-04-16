__copyright__ = "Copyright 2025 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from django.test import TestCase, override_settings
from unittest.mock import patch

from submission import forms, logic, models, views
from utils import setting_handler
from utils.testing import helpers


class TestSubmitAuthors(TestCase):

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
        )
        cls.article = helpers.create_article(
            cls.journal_one,
            owner=cls.kathleen,
            current_step=2,
        )
        setting_handler.save_setting(
            'general',
            'limit_access_to_submission',
            cls.journal_one,
            '',
        )
        setting_handler.save_setting(
            'general',
            'disable_journal_submission',
            cls.journal_one,
            '',
        )
        logic.add_user_as_author(cls.kathleen, cls.article)

    @override_settings(URL_CONFIG='domain')
    def test_submit_authors_get(self):
        self.client.force_login(self.kathleen)
        response = self.client.get(
            f'/submit/{self.article.pk}/authors/',
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(response.context['article'], self.article)
        author, credits, credit_form = response.context['authors'][0]
        self.assertEqual(author, self.kathleen)
        self.assertFalse(credits.exists())
        self.assertTrue(isinstance(credit_form, forms.CreditRecordForm))
        self.assertTrue(isinstance(response.context['form'], forms.AuthorForm))

    @override_settings(URL_CONFIG='domain')
    def test_submit_authors_add_author_existing(self):
        self.client.force_login(self.kathleen)
        post_data = {
            'add_author': '',
            'email': self.eliot.email,
            'first_name': self.eliot.first_name,
            'middle_name': self.eliot.middle_name,
            'last_name': self.eliot.last_name,
        }
        response = self.client.post(
            f'/submit/{self.article.pk}/authors/',
            post_data,
            SERVER_NAME=self.journal_one.domain,
        )
        second_author, _, _ = response.context['authors'][1]
        self.assertEqual(second_author, self.eliot)

    @override_settings(URL_CONFIG='domain')
    def test_submit_authors_add_author_new(self):
        self.client.force_login(self.kathleen)
        post_data = {
            'add_author': '',
            'email': '6cfka43pltcafyzlluxa@example.org',
            'first_name': 'Eric',
            'last_name': 'Hobsbawm',
        }
        response = self.client.post(
            f'/submit/{self.article.pk}/authors/',
            post_data,
            SERVER_NAME=self.journal_one.domain,
        )
        second_author, _, _ = response.context['authors'][1]
        self.assertEqual(second_author.first_name, 'Eric')

    @patch('submission.logic.add_author_from_search')
    @override_settings(URL_CONFIG='domain')
    def test_submit_authors_search_authors(self, logic_add_author):
        self.client.force_login(self.kathleen)
        post_data = {
            'search_authors': '',
            'author_search_text': self.eliot.email,
        }
        response = self.client.post(
            f'/submit/{self.article.pk}/authors/',
            post_data,
            SERVER_NAME=self.journal_one.domain,
        )
        logic_add_author.assert_called()

    @override_settings(URL_CONFIG='domain')
    def test_submit_authors_corr_author(self):
        logic.add_user_as_author(self.eliot, self.article)
        self.client.force_login(self.kathleen)
        post_data = {
            'corr_author': self.eliot.pk,
        }
        response = self.client.post(
            f'/submit/{self.article.pk}/authors/',
            post_data,
            SERVER_NAME=self.journal_one.domain,
        )
        self.article.refresh_from_db()
        self.assertEqual(self.article.correspondence_author, self.eliot)

    @override_settings(URL_CONFIG='domain')
    def test_submit_authors_add_credit(self):
        logic.add_user_as_author(self.eliot, self.article)
        self.client.force_login(self.kathleen)
        post_data = {
            'add_credit': 'writing-original-draft',
            'author_pk': self.eliot.pk,
        }
        self.client.post(
            f'/submit/{self.article.pk}/authors/',
            post_data,
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(
            self.eliot.credits(self.article)[0].role,
            'writing-original-draft',
        )

    @override_settings(URL_CONFIG='domain')
    def test_submit_authors_remove_credit(self):
        # Set up a second author with a credit role
        logic.add_user_as_author(self.eliot, self.article)
        self.eliot.add_credit('writing-original-draft', self.article)

        # Run test
        self.client.force_login(self.kathleen)
        post_data = {
            'remove_credit': 'writing-original-draft',
            'author_pk': self.eliot.pk,
        }
        self.client.post(
            f'/submit/{self.article.pk}/authors/',
            post_data,
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertFalse(self.eliot.credits(self.article).exists())

    @patch('submission.logic.save_author_order')
    @override_settings(URL_CONFIG='domain')
    def test_submit_authors_change_order(self, logic_save_author_order):
        # Add a second author
        logic.add_user_as_author(self.eliot, self.article)

        # Run test
        self.client.force_login(self.kathleen)
        post_data = {
            'change_order': 'up',
            'author_pk': self.eliot.pk,
        }
        self.client.post(
            f'/submit/{self.article.pk}/authors/',
            post_data,
            SERVER_NAME=self.journal_one.domain,
        )
        logic_save_author_order.assert_called()

    @override_settings(URL_CONFIG='domain')
    def test_submit_authors_change_order(self):
        self.client.force_login(self.kathleen)
        post_data = {
            'save_continue': '',
        }
        self.client.post(
            f'/submit/{self.article.pk}/authors/',
            post_data,
            SERVER_NAME=self.journal_one.domain,
        )
        self.article.refresh_from_db()
        self.assertEqual(self.article.current_step, 3)
