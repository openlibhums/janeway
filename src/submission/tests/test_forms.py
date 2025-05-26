__copyright__ = "Copyright 2025 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from django.test import TestCase

from submission import forms


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
