__copyright__ = "Copyright 2025 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from django.test import TestCase, override_settings

from submission import forms
from submission import models as sm_models
from utils.testing import helpers


def extra_sections_hook(form=None, article=None, journal=None, **kwargs):
    """Test double for a plugin's submission_form_init hook: makes all
    of the journal's sections available."""
    form.fields["section"].queryset = sm_models.Section.objects.filter(
        journal=journal,
    )


def lock_section_hook(form=None, article=None, journal=None, **kwargs):
    """Test double for a plugin's submission_form_init hook: narrows the
    choices to the article's own section and locks the field."""
    form.fields["section"].queryset = sm_models.Section.objects.filter(
        pk=article.section_id,
    )
    form.fields["section"].disabled = True


SECTION_HOOK = {
    "submission_form_init": [
        {
            "module": "submission.tests.test_forms",
            "function": "extra_sections_hook",
        },
    ],
}

LOCKED_SECTION_HOOK = {
    "submission_form_init": [
        {
            "module": "submission.tests.test_forms",
            "function": "lock_section_hook",
        },
    ],
}


class ArticleFormTests(TestCase):
    def test_competing_interests_in_edit_article_metadata(self):
        form = forms.EditArticleMetadata()
        self.assertIn(
            "competing_interests",
            form.fields,
            "'competing_interests' should be present in EditArticleMetadata",
        )

    def test_competing_interests_not_in_article_info_submit(self):
        form = forms.ArticleInfoSubmit()
        self.assertNotIn(
            "competing_interests",
            form.fields,
            "'competing_interests' should NOT be present in ArticleInfoSubmit",
        )

    def test_competing_interests_not_in_editor_article_info_submit(self):
        form = forms.EditorArticleInfoSubmit()
        self.assertNotIn(
            "competing_interests",
            form.fields,
            "'competing_interests' should NOT be present in EditorArticleInfoSubmit",
        )


class SubmissionFormSectionHookTests(TestCase):
    """
    Tests for the submission_form_init plugin hook, which passes the
    author-facing submission form to plugins so they can alter it, e.g.
    to make a section closed for public submission available, or to lock
    the section for a commissioned article.
    """

    @classmethod
    def setUpTestData(cls):
        helpers.create_press()
        cls.journal, _ = helpers.create_journals()
        cls.public_section = helpers.create_section(
            cls.journal,
            name="Research Articles",
            plural="Research Articles",
        )
        cls.closed_section = helpers.create_section(
            cls.journal,
            name="Reviews",
            plural="Reviews",
            public_submissions=False,
        )
        cls.licence = helpers.create_licence(
            cls.journal,
            name="Creative Commons 4",
            short_name="CC4",
        )
        cls.article = helpers.create_article(
            cls.journal,
            title="A Commissioned Review",
        )

    @override_settings(PLUGIN_HOOKS=SECTION_HOOK)
    def test_hook_adds_sections_to_author_submit_form(self):
        form = forms.ArticleInfoSubmit(instance=self.article)
        self.assertIn(self.closed_section, form.fields["section"].queryset)
        self.assertIn(self.public_section, form.fields["section"].queryset)

    @override_settings(PLUGIN_HOOKS=SECTION_HOOK)
    def test_hook_section_accepted_on_post(self):
        form = forms.ArticleInfoSubmit(
            {
                "title": "A Commissioned Review",
                "section": self.closed_section.pk,
                "license": self.licence.pk,
                "abstract": "An abstract.",
                "language": "eng",
            },
            instance=self.article,
        )
        form.is_valid()
        self.assertNotIn("section", form.errors)

    def test_without_hook_closed_sections_stay_hidden(self):
        form = forms.ArticleInfoSubmit(instance=self.article)
        self.assertNotIn(self.closed_section, form.fields["section"].queryset)
        self.assertIn(self.public_section, form.fields["section"].queryset)

    @override_settings(PLUGIN_HOOKS=LOCKED_SECTION_HOOK)
    def test_editor_form_unaffected_by_hook(self):
        form = forms.EditorArticleInfoSubmit(instance=self.article)
        self.assertIn(self.closed_section, form.fields["section"].queryset)
        self.assertFalse(form.fields["section"].disabled)

    @override_settings(PLUGIN_HOOKS=LOCKED_SECTION_HOOK)
    def test_lock_hook_disables_section_field(self):
        self.article.section = self.closed_section
        self.article.save()
        form = forms.ArticleInfoSubmit(instance=self.article)
        self.assertTrue(form.fields["section"].disabled)

    @override_settings(PLUGIN_HOOKS=LOCKED_SECTION_HOOK)
    def test_lock_hook_prevents_section_change(self):
        self.article.section = self.closed_section
        self.article.save()
        form = forms.ArticleInfoSubmit(
            {
                "title": "A Commissioned Review",
                "section": self.public_section.pk,
                "license": self.licence.pk,
                "abstract": "An abstract.",
                "language": "eng",
            },
            instance=self.article,
        )
        form.is_valid()
        self.assertNotIn("section", form.errors)
        self.assertEqual(form.cleaned_data["section"], self.closed_section)

    def test_without_lock_hook_field_is_enabled(self):
        form = forms.ArticleInfoSubmit(instance=self.article)
        self.assertFalse(form.fields["section"].disabled)


class CreditRecordFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        helpers.create_roles(["author"])
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.article = helpers.create_article(cls.journal_one)
        cls.author = helpers.create_frozen_author(cls.article)

    def test_form_with_duplicate_data_is_invalid_and_has_error(self):
        post_data = {"role": "writing-original-draft"}
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
