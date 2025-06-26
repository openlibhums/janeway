__copyright__ = "Copyright 2025 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from django.test import TestCase

from submission import forms
from utils.testing import helpers


class ArticleFormTests(TestCase):

    def test_competing_interests_in_edit_article_metadata(self):
        form = forms.EditArticleMetadata()
        self.assertIn(
            'competing_interests',
            form.fields,
            "'competing_interests' should be present in EditArticleMetadata",
        )

    def test_competing_interests_not_in_article_info_submit(self):
        form = forms.ArticleInfoSubmit()
        self.assertNotIn(
            'competing_interests',
            form.fields,
            "'competing_interests' should NOT be present in ArticleInfoSubmit",
        )

    def test_competing_interests_not_in_editor_article_info_submit(self):
        form = forms.EditorArticleInfoSubmit()
        self.assertNotIn(
            'competing_interests',
            form.fields,
            "'competing_interests' should NOT be present in EditorArticleInfoSubmit"
        )


class CreditRecordFormTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        helpers.create_roles(['author'])
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.article = helpers.create_article(cls.journal_one)
        cls.author = helpers.create_frozen_author(cls.article)

    def test_form_with_duplicate_data_is_invalid_and_has_error(self):
        post_data = {
            'role': 'writing-original-draft'
        }
        orig_form = forms.CreditRecordForm(
            post_data,
            frozen_author=self.author,
        )
        orig_form.is_valid()
        record = orig_form.save()
        record.frozen_author = self.author
        record.save()
        form_with_duplicate_data = forms.CreditRecordForm(
            post_data,
            frozen_author=self.author,
        )
        self.assertFalse(form_with_duplicate_data.is_valid())
        self.assertTrue(form_with_duplicate_data.errors)
