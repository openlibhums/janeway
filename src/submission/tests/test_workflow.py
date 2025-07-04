__copyright__ = "Copyright 2025 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from mock import Mock
import os

from django.http import Http404
from django.test import TestCase
from django.utils import translation, timezone
from django.urls.base import clear_script_prefix
from django.conf import settings
from django.shortcuts import reverse
from django.test.utils import override_settings

from core.models import Account, File
from identifiers import logic as id_logic
from journal import models as journal_models
from submission import (
    decorators,
    encoding,
    forms,
    logic,
    models,
)
from utils.forms import clean_orcid_id
from utils.install import update_xsl_files, update_settings, update_issue_types
from utils.shared import clear_cache
from utils.testing import helpers
from utils.testing.helpers import create_galley

FROZEN_DATETIME_2020 = timezone.make_aware(timezone.datetime(2020, 1, 1, 0, 0, 0))
FROZEN_DATETIME_1990 = timezone.make_aware(timezone.datetime(1990, 1, 1, 12, 0, 0))


class SubmissionTests(TestCase):
    roles_path = os.path.join(settings.BASE_DIR, "utils", "install", "roles.json")
    fixtures = [roles_path]

    def test_new_journals_has_submission_configuration(self):
        if not self.journal_one.submissionconfiguration:
            self.fail("Journal does not have a submissionconfiguration object.")

    @classmethod
    def create_authors(cls):
        author_1_data = {
            "email": "one@example.org",
            "is_active": True,
            "password": "this_is_a_password",
            "first_name": "Martin",
            "middle_name": "",
            "last_name": "Eve",
            "department": "English & Humanities",
            "institution": "Birkbeck, University of London",
        }
        author_2_data = {
            "email": "two@example.org",
            "is_active": True,
            "password": "this_is_a_password",
            "first_name": "Mauro",
            "middle_name": "",
            "last_name": "Sanchez",
            "department": "English & Humanities",
            "institution": "Birkbeck, University of London",
        }
        author_1 = helpers.create_author(cls.journal_one, **author_1_data)
        author_2 = helpers.create_author(cls.journal_one, **author_2_data)

        return author_1, author_2

    @classmethod
    def create_sections(cls):
        cls.section_1 = models.Section.objects.create(
            name="Test Public Section",
            journal=cls.journal_one,
        )
        cls.section_2 = models.Section.objects.create(
            name="Test Private Section",
            public_submissions=False,
            journal=cls.journal_one,
        )
        cls.section_3 = models.Section.objects.create(
            journal=cls.journal_one,
        )

    @classmethod
    def setUpTestData(cls):
        """
        Setup the test environment.
        :return: None
        """
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.editor = helpers.create_editor(cls.journal_one)
        cls.press = helpers.create_press()
        cls.create_sections()
        cls.licence = helpers.create_licence(
            journal=cls.journal_one,
            name="Creative Commons Attribution",
            short_name="CC BY",
        )
        cls.article = helpers.create_article(cls.journal_one)

        cls.boolean_field = models.Field.objects.create(
            journal=cls.journal_one,
            name="test_boolean",
            kind="check",
            order=1,
            help_text="Test boolean field",
            required=False,
        )
        cls.text_field = models.Field.objects.create(
            journal=cls.journal_one,
            name="test_text",
            kind="text",
            order=1,
            help_text="Test text field",
            required=False,
        )

    def test_article_image_galley(self):
        article = models.Article.objects.create(
            journal=self.journal_one,
            date_published=FROZEN_DATETIME_2020,
            stage=models.STAGE_PUBLISHED,
        )
        galley_file = File.objects.create(
            article_id=article.pk,
            label="image",
            mime_type="image/jpeg",
            is_galley=True,
        )

        galley = create_galley(article, galley_file)
        galley.label = "image"
        expected = f'<img class="responsive-img" src=/article/{article.pk}/galley/{galley.pk}/download/ alt="image">'

        self.assertEqual(galley.file_content().strip(), expected)

    def test_article_how_to_cite(self):
        issue = journal_models.Issue.objects.create(
            journal=self.journal_one,
            issue="0",
            volume=1,
        )
        article = models.Article.objects.create(
            journal=self.journal_one,
            title="Test article: a test article",
            primary_issue=issue,
            date_published=FROZEN_DATETIME_2020,
            page_numbers="2-4",
        )
        author = models.FrozenAuthor.objects.create(
            article=article,
            first_name="Mauro",
            middle_name="Middle",
            last_name="Sanchez",
        )
        id_logic.generate_crossref_doi_with_pattern(article)

        expected = """
        <p>
         Sanchez, M. M.,
        (2020) “Test article: a test article”,
        <i>Journal One</i> 1, 2-4.
        doi: <a href="https://doi.org/{0}">https://doi.org/{0}</a></p>
        """.format(article.get_doi())
        self.assertHTMLEqual(expected, article.how_to_cite)

    def test_custom_article_how_to_cite(self):
        issue = journal_models.Issue.objects.create(journal=self.journal_one)
        journal_models.Issue
        article = models.Article.objects.create(
            journal=self.journal_one,
            title="Test article: a test article",
            primary_issue=issue,
            date_published=FROZEN_DATETIME_2020,
            page_numbers="2-4",
            custom_how_to_cite="Banana",
        )
        author = models.FrozenAuthor.objects.create(
            article=article,
            first_name="Mauro",
            middle_name="M",
            last_name="Sanchez",
        )
        id_logic.generate_crossref_doi_with_pattern(article)

        expected = "Banana"
        self.assertHTMLEqual(expected, article.how_to_cite)

    def test_funding_is_enabled_decorator_enabled(self):
        request = Mock()
        journal = self.journal_one
        journal.submissionconfiguration.funding = True
        request.journal = journal
        func = Mock()
        decorated = decorators.funding_is_enabled(func)
        decorated(request)
        self.assertTrue(func.called, "Funding pages not available when they should be")

    def test_funding_is_enabled_decorator_disabled(self):
        request = Mock()
        journal = self.journal_one
        journal.submissionconfiguration.funding = False
        request.journal = journal
        func = Mock()
        decorated = decorators.funding_is_enabled(func)
        with self.assertRaises(
            Http404, msg="Funding pages available when they shouldn't"
        ):
            decorated(request)

    def test_snapshot_as_author_metadata_do_not_override(self):
        article = models.Article.objects.create(
            journal=self.journal_one,
            title="Test article: a test article",
        )
        author, _ = self.create_authors()

        frozen = author.snapshot_as_author(article)
        new_department = "New department"
        frozen.department = new_department
        frozen.save()
        author.snapshot_as_author(article, force_update=False)

        self.assertEqual(
            frozen.department,
            new_department,
            msg="Frozen author info has been overridden by snapshot_as_author",
        )

    def test_snapshot_as_author_metadata_override(self):
        article = models.Article.objects.create(
            journal=self.journal_one,
            title="Test article: a test article",
        )
        author, _ = self.create_authors()

        author.snapshot_as_author(article)
        new_department = "New department"
        for frozen_author in article.frozen_authors():
            frozen_author.department = new_department
            frozen_author.save()
        frozen = author.snapshot_as_author(article, force_update=True)

        self.assertEqual(
            frozen.department,
            author.department,
            msg="Frozen author edits have not been overridden by snapshot_as_author",
        )

    def test_frozen_author_prefix(self):
        article = models.Article.objects.create(
            journal=self.journal_one,
            title="Test article: a test article",
        )
        author, _ = self.create_authors()
        author.snapshot_as_author(article)

        prefix = "Lord"
        article.frozen_authors().update(name_prefix=prefix)
        frozen = article.frozen_authors().all()[0]

        self.assertTrue(frozen.full_name().startswith(prefix))

    def test_frozen_author_suffix(self):
        article = models.Article.objects.create(
            journal=self.journal_one,
            title="Test article: a test article",
        )
        author, _ = self.create_authors()
        author.snapshot_as_author(article)

        suffix = "Jr"
        article.frozen_authors().update(name_suffix=suffix)
        frozen = article.frozen_authors().all()[0]

        self.assertTrue(frozen.full_name().endswith(suffix))

    def test_snapshot_as_author_order(self):
        article = models.Article.objects.create(
            journal=self.journal_one,
            title="Test article: a test article",
        )
        author_1, author_2 = self.create_authors()
        frozen_author_1 = author_1.snapshot_as_author(article)
        frozen_author_2 = author_2.snapshot_as_author(article)
        self.assertListEqual(
            [frozen_author_1.order, frozen_author_2.order],
            [0, 1],
            msg="Authors frozen in the wrong order",
        )

    def test_article_keyword_default_order(self):
        article = models.Article.objects.create(
            journal=self.journal_one,
            title="Test article: a test of keywords",
        )
        keywords = ["one", "two", "three", "four"]
        for i, kw in enumerate(keywords):
            kw_obj = models.Keyword.objects.create(word=kw)
            models.KeywordArticle.objects.get_or_create(keyword=kw_obj, article=article)

        self.assertEqual(
            keywords,
            [kw.word for kw in article.keywords.all()],
        )

    def test_article_keyword_add(self):
        article = models.Article.objects.create(
            journal=self.journal_one,
            title="Test article: a test of keywords",
        )
        keywords = ["one", "two", "three", "four"]
        for i, kw in enumerate(keywords):
            kw_obj = models.Keyword.objects.create(word=kw)
            article.keywords.add(kw_obj)

        self.assertEqual(
            keywords,
            [kw.word for kw in article.keywords.all()],
        )

    def test_article_keyword_remove(self):
        article = models.Article.objects.create(
            journal=self.journal_one,
            title="Test article: a test of keywords",
        )
        keywords = ["one", "two", "three", "four"]
        kw_objs = []
        for i, kw in enumerate(keywords):
            kw_obj = models.Keyword.objects.create(word=kw)
            kw_objs.append(kw_obj)
            article.keywords.add(kw_obj)

        article.keywords.remove(kw_objs[1])
        keywords.pop(1)

        self.assertEqual(
            keywords,
            [kw.word for kw in article.keywords.all()],
        )

    def test_article_keyword_clear(self):
        article = models.Article.objects.create(
            journal=self.journal_one,
            title="Test article: a test of keywords",
        )
        keywords = ["one", "two", "three", "four"]
        for i, kw in enumerate(keywords):
            kw_obj = models.Keyword.objects.create(word=kw)
            article.keywords.add(kw_obj)
        article.keywords.clear()

        self.assertEqual(
            [],
            [kw.word for kw in article.keywords.all()],
        )

    def test_edit_section(self):
        """Ensures editors can select sections that are not submissible"""
        article = models.Article.objects.create(
            journal=self.journal_one,
            title="Test article: a test of sections",
        )
        with translation.override("en"):
            section = models.Section.objects.create(
                journal=self.journal_one,
                name="section",
                public_submissions=False,
            )
            form = forms.ArticleInfo(instance=article)
            self.assertTrue(section in form.fields["section"].queryset)

    def test_select_disabled_section_submit(self):
        article = models.Article.objects.create(
            journal=self.journal_one,
            title="Test article: a test of sections",
        )
        with translation.override("en"):
            section = models.Section.objects.create(
                journal=self.journal_one,
                name="section",
                public_submissions=False,
            )
            form = forms.ArticleInfoSubmit(instance=article)
            self.assertTrue(section not in form.fields["section"].queryset)

    @override_settings(URL_CONFIG="domain")
    def test_submit_info_view_form_selection_editor(self):
        article = models.Article.objects.create(
            journal=self.journal_one,
            title="Test article: a test of sections",
        )
        with translation.override("en"):
            section = models.Section.objects.create(
                journal=self.journal_one,
                name="section",
                public_submissions=False,
            )
        self.client.force_login(
            self.editor,
        )
        clear_script_prefix()
        response = self.client.get(
            reverse("submit_info", kwargs={"article_id": article.pk}),
            SERVER_NAME="testserver",
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, section.__str__())

    @override_settings(URL_CONFIG="domain")
    def test_submit_info_view_form_selection_author(self):
        author_1, _ = self.create_authors()
        clear_cache()
        article = models.Article.objects.create(
            journal=self.journal_one,
            title="Test article: a test of author sections",
            owner=author_1,
        )
        with translation.override("en"):
            section = models.Section.objects.create(
                journal=self.journal_one,
                name="Test Section",
                public_submissions=False,
            )
        self.client.force_login(
            author_1,
        )
        clear_script_prefix()
        response = self.client.get(
            reverse("submit_info", kwargs={"article_id": article.pk}),
            SERVER_NAME="testserver",
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, section.__str__())

    def test_article_issue_title(self):
        from utils.testing import helpers

        issue = helpers.create_issue(
            self.journal_one,
            vol=5,
            number=4,
        )
        issue.issue_title = "Fall 2025"
        from utils.logic import get_aware_datetime

        issue.date = get_aware_datetime("2025-10-01")
        issue.save()

        article = models.Article.objects.create(
            journal=self.journal_one,
            title="Test article: A test of page numbers",
            first_page=3,
            last_page=5,
            primary_issue=issue,
        )

        expected_article_issue_title = "Volume 5 • Issue 4 • 2025 • Fall 2025 • 3–5"
        self.assertEqual(expected_article_issue_title, article.issue_title)

        article.page_numbers = "x–ix"
        article.save()
        expected_article_issue_title = "Volume 5 • Issue 4 • 2025 • Fall 2025 • x–ix"
        self.assertEqual(expected_article_issue_title, article.issue_title)

        article.first_page = None
        article.last_page = None
        article.page_numbers = None
        article.total_pages = 1
        article.save()
        expected_article_issue_title = "Volume 5 • Issue 4 • 2025 • Fall 2025 • 1 page"
        self.assertEqual(expected_article_issue_title, article.issue_title)
    
    def test_article_issue_title_a11y(self):
        from utils.testing import helpers
        issue = helpers.create_issue(
            self.journal_one,
            vol=5,
            number=4,
        )
        issue.issue_title = 'Fall 2025'
        from utils.logic import get_aware_datetime
        issue.date = get_aware_datetime('2025-10-01')
        issue.save()

        article = models.Article.objects.create(
            journal=self.journal_one,
            title="Test article: A test of page numbers",
            first_page=3,
            last_page=5,
            primary_issue=issue,
        )

        expected_article_issue_title = 'Volume 5, Issue 4, ' \
                                       '2025, Fall 2025, 3–5'
        self.assertEqual(expected_article_issue_title, article.issue_title_a11y)

        article.page_numbers='x–ix'
        article.save()
        expected_article_issue_title = 'Volume 5, Issue 4, ' \
                                       '2025, Fall 2025, x–ix'
        self.assertEqual(expected_article_issue_title, article.issue_title_a11y)

        article.first_page = None
        article.last_page = None
        article.page_numbers = None
        article.total_pages = 1
        article.save()
        expected_article_issue_title = 'Volume 5, Issue 4, ' \
                                       '2025, Fall 2025, 1 page'
        self.assertEqual(expected_article_issue_title, article.issue_title_a11y)


    def test_url_based_orcid_cleaned(self):
        clean_orcid = clean_orcid_id("https://orcid.org/0000-0003-2126-266X")
        self.assertEqual(
            clean_orcid,
            "0000-0003-2126-266X",
        )

    def test_orcid_value_error_raised(self):
        with self.assertRaises(ValueError):
            clean_orcid_id("Mauro-sfak-orci-dtst")

    def test_author_form_harmful_inputs(self):
        harmful_string = '<span onClick="alert()"> This are not the droids you are looking for </span>'
        for i, attr in enumerate(
            {
                "first_name",
                "last_name",
                "middle_name",
                "name_prefix",
                "name_suffix",
            }
        ):
            form = forms.EditFrozenAuthor(
                {
                    "first_name": "Andy",
                    "last_name": "Byers",
                    "frozen_biography": "Andy",
                    "frozen_email": f"andy{i}@janeway.systems",
                    **{attr: harmful_string},
                }
            )
            self.assertFalse(
                form.is_valid(), f"Harmful code injected into field '{attr}'"
            )

    @override_settings(URL_CONFIG="domain")
    def test_article_encoding_bibtex(self):
        article = helpers.create_article(
            journal=self.journal_one,
            title="Test article: a test article",
            stage="Published",
            abstract="test_abstract",
            date_published=FROZEN_DATETIME_1990,
        )
        helpers.create_issue(self.journal_one, 2, 1, articles=[article])
        author_a, author_b = self.create_authors()
        author_a.snapshot_as_author(article)
        author_b.snapshot_as_author(article)

        # we have to clear cache here due to function cache relying on primary
        # keys being used for cache keys, which in tests will always be 1
        clear_cache()
        bibtex = encoding.encode_article_as_bibtex(article)
        expected = """
            @article{TST%s,
                author = {Martin Eve AND Mauro Sanchez},
                title = {Test article: a test article},
                volume = {2},
                year = {1990},
                url = {http://testserver/article/id/%s/},
                issue = {1},
                abstract = {test_abstract},
                month = {1},
                issn = {%s},
                publisher ={},
                journal = {%s}
            }
        """ % (article.pk, article.pk, article.journal.issn, article.journal.name)
        bibtex_lines = [line.strip() for line in bibtex.splitlines() if line.strip()]
        expected_lines = [
            line.strip() for line in expected.splitlines() if line.strip()
        ]
        self.assertEqual(bibtex_lines, expected_lines)

    @override_settings(URL_CONFIG="domain")
    def test_article_encoding_ris(self):
        article = helpers.create_article(
            journal=self.journal_one,
            title="Test article: A RIS export test case",
            stage="Published",
            abstract="test_abstract",
            date_published=FROZEN_DATETIME_1990,
        )
        helpers.create_issue(self.journal_one, 2, 2, articles=[article])
        author_a, author_b = self.create_authors()
        author_a.snapshot_as_author(article)
        author_b.snapshot_as_author(article)

        ris = encoding.encode_article_as_ris(article)
        expected = """
            TY  - JOUR
            AB  - test_abstract
            AU  - Martin Eve
            AU  - Mauro Sanchez
            PA  - 1990
            DA  - 1990/01/01
            IS  - 2
            VL  - 2
            PB  -
            PY  - 1990
            TI  - Test article: A RIS export test case
            T2  - {journal_name}
            UR  - http://testserver/article/id/{article_id}/
            ER  -
        """.format(article_id=article.pk, journal_name=article.journal.name)
        ris_lines = [line.strip() for line in ris.splitlines() if line.strip()]
        expected_lines = [
            line.strip() for line in expected.splitlines() if line.strip()
        ]
        self.assertEqual(ris_lines, expected_lines)

    def test_page_range_first_last(self):
        article = models.Article.objects.create(
            journal=self.journal_one,
            title="Test article: A test of page ranges",
            first_page=3,
            last_page=5,
        )
        self.assertEqual(article.page_range, "3–5")

    def test_page_range_first_only(self):
        article = models.Article.objects.create(
            journal=self.journal_one,
            title="Test article: A test of page ranges",
            first_page=3,
        )
        self.assertEqual(article.page_range, "3")

    def test_page_range_custom(self):
        article = models.Article.objects.create(
            journal=self.journal_one,
            title="Test article: A test of page ranges",
            first_page=3,
            last_page=5,
            page_numbers="custom",
        )
        self.assertEqual(article.page_range, "custom")

    def test_editor_sees_non_public_sections(self):
        clear_cache()
        article = models.Article.objects.create(
            journal=self.journal_one,
            title="Test article: Testing non public sections",
            current_step=2,
            owner=self.editor,
        )
        self.client.force_login(
            self.editor,
        )
        clear_script_prefix()
        response = self.client.get(
            reverse(
                "submit_info",
                kwargs={"article_id": article.pk},
            ),
            SERVER_NAME="testserver",
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            self.section_2.display_name_public_submission(),
        )

    def test_author_doesnt_see_non_public_section(self):
        author = helpers.create_author(self.journal_one)
        article = models.Article.objects.create(
            journal=self.journal_one,
            title="Test article: Testing public sections",
            current_step=2,
            owner=author,
        )
        self.client.force_login(
            author,
        )
        clear_script_prefix()
        response = self.client.get(
            reverse(
                "submit_info",
                kwargs={"article_id": article.pk},
            ),
            SERVER_NAME="testserver",
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(
            response,
            self.section_2.display_name_public_submission(),
        )

    def test_boolean_field_unchecked_sets_false(self):
        post_data = {
            "title": "Updated Title",
            "absract": "Test Abstract",
            "language": "eng",
            "section": self.section_1.pk,
            "license": self.licence.pk,
        }

        request = helpers.get_request(journal=self.journal_one)
        request.POST = post_data

        form = forms.ArticleInfo(
            data=post_data,
            instance=self.article,
        )

        if form.is_valid():
            form.save(
                request=request,
            )
        else:
            self.fail(f"Form is invalid: {form.errors}")

        field_answer = models.FieldAnswer.objects.get(
            article=self.article,
            field=self.boolean_field,
        )
        self.assertEqual(field_answer.answer, "")

    def test_boolean_field_unchecked_sets_true(self):
        post_data = {
            "title": "Updated Title",
            "absract": "Test Abstract",
            "language": "eng",
            "section": self.section_1.pk,
            "license": self.licence.pk,
            "test_boolean": "on",
        }

        request = helpers.get_request(journal=self.journal_one)
        request.POST = post_data

        form = forms.ArticleInfo(
            data=post_data,
            instance=self.article,
        )

        if form.is_valid():
            form.save(
                request=request,
            )
        else:
            self.fail(f"Form is invalid: {form.errors}")

        field_answer = models.FieldAnswer.objects.get(
            article=self.article,
            field=self.boolean_field,
        )
        self.assertEqual(field_answer.answer, "on")

    def test_text_field_sets(self):
        post_data = {
            "title": "Updated Title",
            "absract": "Test Abstract",
            "language": "eng",
            "section": self.section_1.pk,
            "license": self.licence.pk,
            "test_text": "Sometimes first contact is last contact.",
        }

        request = helpers.get_request(journal=self.journal_one)
        request.POST = post_data

        form = forms.ArticleInfo(
            data=post_data,
            instance=self.article,
        )

        if form.is_valid():
            form.save(
                request=request,
            )
        else:
            self.fail(f"Form is invalid: {form.errors}")

        field_answer = models.FieldAnswer.objects.get(
            article=self.article,
            field=self.text_field,
        )
        self.assertEqual(
            field_answer.answer,
            "Sometimes first contact is last contact.",
        )
