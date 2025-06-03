__copyright__ = "Copyright 2025 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from django.shortcuts import reverse
from django.test import TestCase, override_settings
from unittest.mock import patch

from submission import forms, logic, models, views
from utils import setting_handler
from utils.testing import helpers


class TestSubmitViewsBase(TestCase):

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
        cls.kathleen_author = cls.kathleen.snapshot_self(cls.article)
        cls.article.correspondence_author = cls.kathleen
        cls.article.save()


class TestSubmitAuthors(TestSubmitViewsBase):

    @override_settings(URL_CONFIG='domain')
    def test_submit_authors_get(self):
        self.client.force_login(self.kathleen)
        response = self.client.get(
            reverse('submit_authors', kwargs={'article_id': self.article.pk}),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(response.context['article'], self.article)
        article = response.context['article']
        self.assertIn(self.kathleen_author, article.authors_and_credits())
        credits = article.authors_and_credits()[self.kathleen_author]
        self.assertFalse(credits.exists())
        self.assertTrue(
            isinstance(response.context['new_author_form'], forms.EditFrozenAuthor)
        )

    @override_settings(URL_CONFIG='domain')
    def test_submit_authors_add_author_existing(self):
        self.client.force_login(self.kathleen)
        post_data = {
            'add_author': '',
            'frozen_email': self.eliot.email,
            'first_name': self.eliot.first_name,
            'middle_name': self.eliot.middle_name,
            'last_name': self.eliot.last_name,
        }
        response = self.client.post(
            reverse('submit_authors', kwargs={'article_id': self.article.pk}),
            post_data,
            SERVER_NAME=self.journal_one.domain,
        )
        second_author = response.context['article'].frozenauthor_set.all()[1]
        self.assertEqual(second_author, self.eliot.frozen_author(self.article))

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
            reverse('submit_authors', kwargs={'article_id': self.article.pk}),
            post_data,
            SERVER_NAME=self.journal_one.domain,
        )
        second_author = response.context['article'].frozenauthor_set.all()[1]
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
            reverse('submit_authors', kwargs={'article_id': self.article.pk}),
            post_data,
            SERVER_NAME=self.journal_one.domain,
        )
        logic_add_author.assert_called()

    @override_settings(URL_CONFIG='domain')
    def test_submit_authors_corr_author(self):
        self.eliot.snapshot_self(self.article)
        self.client.force_login(self.kathleen)
        post_data = {
            'corr_author': self.eliot.pk,
        }
        response = self.client.post(
            reverse('submit_authors', kwargs={'article_id': self.article.pk}),
            post_data,
            SERVER_NAME=self.journal_one.domain,
        )
        self.article.refresh_from_db()
        self.assertEqual(self.article.correspondence_author, self.eliot)

    @patch('submission.logic.save_frozen_author_order')
    @override_settings(URL_CONFIG='domain')
    def test_submit_authors_change_order(self, logic_save_frozen_author_order):
        # Add a second author
        eliot_author = self.eliot.snapshot_self(self.article)

        # Run test
        self.client.force_login(self.kathleen)
        post_data = {
            'change_order': 'up',
            'author_pk': self.eliot.pk,
        }
        self.client.post(
            reverse('submit_authors', kwargs={'article_id': self.article.pk}),
            post_data,
            SERVER_NAME=self.journal_one.domain,
        )
        logic_save_frozen_author_order.assert_called()

    @override_settings(URL_CONFIG='domain')
    def test_submit_authors_continue(self):
        self.client.force_login(self.kathleen)
        post_data = {
            'save_continue': '',
        }
        self.client.post(
            reverse('submit_authors', kwargs={'article_id': self.article.pk}),
            post_data,
            SERVER_NAME=self.journal_one.domain,
        )
        self.article.refresh_from_db()
        self.assertEqual(self.article.current_step, 3)

    @override_settings(
        URL_CONFIG='domain',
        DUMMY_EMAIL_DOMAIN='testing.example.org'
    )
    def test_delete_author_but_they_are_only_correspondence_author(self):
        # Add a second author that does not have a real email address
        self.eliot.email = 'notreal@testing.example.org'
        self.eliot.save()
        self.eliot.snapshot_self(self.article)

        # Run test
        self.client.force_login(self.kathleen)
        post_data = {}
        self.client.post(
            reverse(
                'submission_delete_frozen_author',
                kwargs={
                    'article_id': self.article.pk,
                    'author_id': self.kathleen.frozen_author(self.article).pk,
                },
            ),
            post_data,
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertIn(self.kathleen, self.article.author_accounts)
        self.assertEqual(self.article.correspondence_author, self.kathleen)

    @override_settings(URL_CONFIG='domain', DUMMY_EMAIL_DOMAIN='testing')
    def test_delete_author(self):
        # Add a second author and make them corr author
        eliot_author = self.eliot.snapshot_self(self.article)
        self.article.correspondence_author = self.eliot
        self.article.save()

        # Run test
        self.client.force_login(self.kathleen)
        post_data = {}
        self.client.post(
            reverse(
                'submission_delete_frozen_author',
                kwargs={
                    'article_id': self.article.pk,
                    'author_id': eliot_author.pk,
                },
            ),
            post_data,
            SERVER_NAME=self.journal_one.domain,
        )
        self.article.refresh_from_db()
        self.assertNotIn(self.eliot, self.article.author_accounts)
        self.assertEqual(self.article.correspondence_author, self.kathleen)


class TestEditAuthor(TestSubmitViewsBase):

    @override_settings(URL_CONFIG='domain')
    def test_edit_author_get(self):
        self.client.force_login(self.kathleen)
        setting_handler.save_setting(
            'general',
            'use_credit',
            self.journal_one,
            'on',
        )
        get_data = {}
        response = self.client.get(
            reverse(
                'submission_edit_author',
                kwargs={
                    'article_id': self.article.pk,
                    'author_id': self.kathleen_author.pk,
                },
            ),
            get_data,
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(response.context['article'], self.article)
        self.assertEqual(response.context['author'], self.kathleen_author)
        self.assertEqual(response.context['form'], None)
        self.assertTrue(
            isinstance(response.context['credit_form'], forms.CreditRecordForm)
        )

    @override_settings(URL_CONFIG='domain')
    def test_edit_author_edit_author(self):
        self.client.force_login(self.kathleen)
        get_data = {
            'edit_author': '',
        }
        response = self.client.get(
            reverse(
                'submission_edit_author',
                kwargs={
                    'article_id': self.article.pk,
                    'author_id': self.kathleen_author.pk,
                },
            ),
            get_data,
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertTrue(
            isinstance(response.context['form'], forms.EditFrozenAuthor)
        )
        self.assertEqual(
            response.context['form'].instance,
            self.kathleen_author,
        )

    @override_settings(URL_CONFIG='domain')
    def test_edit_author_save_author(self):
        self.client.force_login(self.kathleen)
        post_data = {
            'save_author': '',
            'first_name': 'K.',
        }
        self.client.post(
            reverse(
                'submission_edit_author',
                kwargs={
                    'article_id': self.article.pk,
                    'author_id': self.kathleen_author.pk,
                },
            ),
            post_data,
            SERVER_NAME=self.journal_one.domain,
        )
        self.kathleen_author.refresh_from_db()
        self.assertEqual(
            self.kathleen_author.first_name,
            'K.',
        )

    @override_settings(URL_CONFIG='domain')
    def test_edit_author_add_credit(self):
        eliot_author = self.eliot.snapshot_self(self.article)
        self.client.force_login(self.kathleen)
        post_data = {
            'add_credit': '',
            'role': 'writing-original-draft',
        }
        self.client.post(
            reverse(
                'submission_edit_author',
                kwargs={
                    'article_id': self.article.pk,
                    'author_id': eliot_author.pk,
                },
            ),
            post_data,
            SERVER_NAME=self.journal_one.domain,
        )
        eliot_author.refresh_from_db()
        self.assertEqual(
            eliot_author.credits[0].role,
            'writing-original-draft',
        )

    @override_settings(URL_CONFIG='domain')
    def test_edit_author_remove_credit(self):
        # Set up a second author with a credit role
        eliot_author = self.eliot.snapshot_self(self.article)
        writing_credit = eliot_author.add_credit('writing-original-draft')

        # Run test
        self.client.force_login(self.kathleen)
        post_data = {
            'remove_credit': 'writing-original-draft',
            'credit_pk': writing_credit.pk,
        }
        self.client.post(
            reverse(
                'submission_edit_author',
                kwargs={
                    'article_id': self.article.pk,
                    'author_id': eliot_author.pk,
                },
            ),
            post_data,
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertFalse(eliot_author.credits.exists())
