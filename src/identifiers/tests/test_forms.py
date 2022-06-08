from django.test import TestCase

from identifiers import forms
from utils.testing import helpers
from utils.setting_handler import save_setting


class TestForms(TestCase):

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

        cls.article_one = helpers.create_article(cls.journal_one, with_author=True)
        cls.article_two = helpers.create_article(cls.journal_two, with_author=True)
        cls.article_three = helpers.create_article(cls.journal_one, with_author=True)

    def test_add_doi(self):
        form = forms.IdentifierForm(
            {
                'id_type': 'doi',
                'identifier': '10.1234/1234',
                'enabled': True,
            },
            article=self.article_one,
        )
        self.assertTrue(
            form.is_valid()
        )

    def test_duplicate_doi_article(self):
        """
        Tests that you can't have a duplicate DOI on the same article.
        """
        form_one = forms.IdentifierForm(
            {
                'id_type': 'doi',
                'identifier': '10.1234/1234',
                'enabled': True,
            },
            article=self.article_one,
        )
        form_two = forms.IdentifierForm(
            {
                'id_type': 'doi',
                'identifier': '10.1234/1234',
                'enabled': True,
            },
            article=self.article_one,
        )

        form_one.save()
        self.assertFalse(
            form_two.is_valid(),
        )

    def test_duplicate_doi_journal(self):
        """
        Tests that you can't have duplicate DOIs across journals.
        """
        form_one = forms.IdentifierForm(
            {
                'id_type': 'doi',
                'identifier': '10.1234/1234',
                'enabled': True,
            },
            article=self.article_one,
        )
        form_two = forms.IdentifierForm(
            {
                'id_type': 'doi',
                'identifier': '10.1234/1234',
                'enabled': True,
            },
            article=self.article_two,
        )

        form_one.save()
        self.assertFalse(
            form_two.is_valid(),
        )

    def test_other_ident_article(self):
        """
        Tests that you cannot have duplicate non DOI idents in the same article.
        """
        form_one = forms.IdentifierForm(
            {
                'id_type': 'pubid',
                'identifier': '1234',
                'enabled': True,
            },
            article=self.article_one,
        )
        form_two = forms.IdentifierForm(
            {
                'id_type': 'pubid',
                'identifier': '1234',
                'enabled': True,
            },
            article=self.article_one,
        )

        form_one.save()
        self.assertFalse(
            form_two.is_valid(),
        )

    def test_other_ident_journal(self):
        """
        Tests that you cannot have duplicate non DOI idents in the same journal.
        """
        form_one = forms.IdentifierForm(
            {
                'id_type': 'pubid',
                'identifier': '1234',
                'enabled': True,
            },
            article=self.article_one,
        )
        form_two = forms.IdentifierForm(
            {
                'id_type': 'pubid',
                'identifier': '1234',
                'enabled': True,
            },
            article=self.article_three,
        )

        form_one.save()
        self.assertFalse(
            form_two.is_valid(),
        )

    def test_other_ident_two_journals(self):
        """
        Tests that you can have duplicate non DOI idents on different journals.
        """
        form_one = forms.IdentifierForm(
            {
                'id_type': 'pubid',
                'identifier': '1234',
                'enabled': True,
            },
            article=self.article_one,
        )
        form_two = forms.IdentifierForm(
            {
                'id_type': 'pubid',
                'identifier': '1234',
                'enabled': True,
            },
            article=self.article_two,
        )

        form_one.save()
        self.assertTrue(
            form_two.is_valid(),
        )


