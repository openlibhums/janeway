__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
from datetime import datetime
from dateutil import parser as dateparser
from mock import Mock
import os

from django.core.management import call_command
from django.http import Http404
from django.test import TestCase, TransactionTestCase
from django.utils import translation
from django.urls.base import clear_script_prefix
from django.conf import settings
from django.shortcuts import reverse
from django.test.utils import override_settings
import swapper

from core.models import Account, File, Galley
from identifiers import logic as id_logic
from journal import models as journal_models
from submission import (
    decorators,
    encoding,
    forms,
    logic,
    models,
)
from utils.install import update_xsl_files, update_settings, update_issue_types
from utils.testing import helpers
from utils.testing.helpers import create_galley, request_context


# Create your tests here.
class SubmissionTests(TestCase):
    roles_path = os.path.join(
        settings.BASE_DIR,
        'utils',
        'install',
        'roles.json'
    )
    fixtures = [roles_path]

    def test_new_journals_has_submission_configuration(self):
        if not self.journal_one.submissionconfiguration:
            self.fail('Journal does not have a submissionconfiguration object.')

    @staticmethod
    def create_journal():
        """
        Creates a dummy journal for testing
        :return: a journal
        """
        update_xsl_files()
        update_settings()
        journal_one = journal_models.Journal(code="TST", domain="testserver")
        journal_one.title = "Test Journal: A journal of tests"
        journal_one.save()
        update_issue_types(journal_one)

        return journal_one

    @staticmethod
    def create_authors():
        author_1_data = {
            'is_active': True,
            'password': 'this_is_a_password',
            'salutation': 'Prof.',
            'first_name': 'Martin',
            'last_name': 'Eve',
            'department': 'English & Humanities',
            'institution': 'Birkbeck, University of London',
        }
        author_2_data = {
            'is_active': True,
            'password': 'this_is_a_password',
            'salutation': 'Sr.',
            'first_name': 'Mauro',
            'last_name': 'Sanchez',
            'department': 'English & Humanities',
            'institution': 'Birkbeck, University of London',
        }
        author_1 = Account.objects.create(email="1@t.t", **author_1_data)
        author_2 = Account.objects.create(email="2@t.t", **author_2_data)

        return author_1, author_2

    def setUp(self):
        """
        Setup the test environment.
        :return: None
        """
        self.journal_one = self.create_journal()
        self.editor = helpers.create_editor(self.journal_one)
        self.press = helpers.create_press()

    def test_article_image_galley(self):
        article = models.Article.objects.create(
            journal=self.journal_one,
            date_published=dateparser.parse("2020-01-01"),
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
            journal = self.journal_one,
            title="Test article: a test article",
            primary_issue=issue,
            date_published=dateparser.parse("2020-01-01"),
            page_numbers = "2-4"
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
        <i>Janeway JS</i> 1, 2-4.
        doi: <a href="https://doi.org/{0}">https://doi.org/{0}</a></p>
        """.format(article.get_doi())
        self.assertHTMLEqual(expected, article.how_to_cite)

    def test_custom_article_how_to_cite(self):
        issue = journal_models.Issue.objects.create(journal=self.journal_one)
        journal_models.Issue
        article = models.Article.objects.create(
            journal = self.journal_one,
            title="Test article: a test article",
            primary_issue=issue,
            date_published=dateparser.parse("2020-01-01"),
            page_numbers = "2-4",
            custom_how_to_cite = "Banana",
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
        self.assertTrue(func.called,
            "Funding pages not available when they should be")

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

    def test_snapshot_author_metadata_correctly(self):
        article = models.Article.objects.create(
            journal = self.journal_one,
            title="Test article: a test article",
        )
        author, _ = self.create_authors()
        logic.add_user_as_author(author, article)

        article.snapshot_authors()
        frozen = article.frozen_authors().all()[0]
        keys = {'first_name', 'last_name', 'department', 'institution'}

        self.assertDictEqual(
            {k: getattr(author, k) for k in keys},
            {k: getattr(frozen, k) for k in keys},
        )

    def test_snapshot_author_order_correctly(self):
        article = models.Article.objects.create(
            journal = self.journal_one,
            title="Test article: a test article",
        )
        author_1, author_2 = self.create_authors()
        logic.add_user_as_author(author_1, article)
        logic.add_user_as_author(author_2, article)

        article.snapshot_authors()
        frozen = article.frozen_authors().all()
        self.assertListEqual(
            [author_1, author_2],
            [f.author for f in article.frozen_authors().order_by("order")],
            msg="Authors frozen in the wrong order",
        )

    def test_snapshot_author_metadata_do_not_override(self):
        article = models.Article.objects.create(
            journal = self.journal_one,
            title="Test article: a test article",
        )
        author, _ = self.create_authors()
        logic.add_user_as_author(author, article)

        article.snapshot_authors()
        frozen = article.frozen_authors().all()[0]
        new_department = "New department"
        frozen.department = new_department
        frozen.save()
        article.snapshot_authors(force_update=False)

        self.assertEqual(
            frozen.department, new_department,
            msg="Frozen author edits have been overriden by snapshot_authors",
        )

    def test_snapshot_author_metadata_override(self):
        article = models.Article.objects.create(
            journal = self.journal_one,
            title="Test article: a test article",
        )
        author, _ = self.create_authors()
        logic.add_user_as_author(author, article)

        article.snapshot_authors()
        new_department = "New department"
        article.frozen_authors().update(department=new_department)
        article.snapshot_authors(force_update=True)
        frozen = article.frozen_authors().all()[0]

        self.assertEqual(
            frozen.department, author.department,
            msg="Frozen author edits have been overriden by snapshot_authors",
        )

    def test_frozen_author_prefix(self):
        article = models.Article.objects.create(
            journal=self.journal_one,
            title="Test article: a test article",
        )
        author, _ = self.create_authors()
        logic.add_user_as_author(author, article)
        article.snapshot_authors()

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
        logic.add_user_as_author(author, article)
        article.snapshot_authors()

        suffix = "Jr"
        article.frozen_authors().update(name_suffix=suffix)
        frozen = article.frozen_authors().all()[0]

        self.assertTrue(frozen.full_name().endswith(suffix))

    def test_snapshot_author_order_author_added_later(self):
        article = models.Article.objects.create(
            journal = self.journal_one,
            title="Test article: a test article",
        )
        author_1, author_2 = self.create_authors()
        logic.add_user_as_author(author_1, article)
        logic.add_user_as_author(author_2, article)
        no_order_author = Account.objects.create(
            email="no_order@t.t",
            first_name="no order",
            last_name="no order",
        )
        article.authors.add(no_order_author)

        article.snapshot_authors()
        frozen = article.frozen_authors().all()
        self.assertListEqual(
            [author_1, author_2, no_order_author],
            [f.author for f in article.frozen_authors().order_by("order")],
            msg="Authors frozen in the wrong order",
        )

    def test_article_keyword_default_order(self):
        article = models.Article.objects.create(
            journal = self.journal_one,
            title="Test article: a test of keywords",
        )
        keywords = ["one", "two", "three", "four"]
        for i, kw in enumerate(keywords):
            kw_obj = models.Keyword.objects.create(word=kw)
            models.KeywordArticle.objects.get_or_create(
                keyword=kw_obj,
                article=article
            )

        self.assertEqual(
            keywords,
            [kw.word for kw in article.keywords.all()],
        )

    def test_article_keyword_add(self):
        article = models.Article.objects.create(
            journal = self.journal_one,
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
            journal = self.journal_one,
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
            journal = self.journal_one,
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
        """ Ensures editors can select sections that are not submissible"""
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

    @override_settings(URL_CONFIG='domain')
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
            reverse('submit_info', kwargs={'article_id': article.pk}),
            SERVER_NAME="testserver",
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, section.__str__())

    @override_settings(URL_CONFIG='domain')
    def test_submit_info_view_form_selection_author(self):
        author_1, author_2 = self.create_authors()
        article = models.Article.objects.create(
            journal=self.journal_one,
            title="Test article: a test of author sections",
            owner=author_1,
        )
        with translation.override("en"):
            section = models.Section.objects.create(
                journal=self.journal_one,
                name="section",
                public_submissions=False,
            )
        self.client.force_login(
            author_1,
        )
        clear_script_prefix()
        response = self.client.get(
            reverse('submit_info', kwargs={'article_id': article.pk}),
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

        expected_article_issue_title = 'Volume 5 • Issue 4 • ' \
                                       '2025 • Fall 2025 • 3–5'
        self.assertEqual(expected_article_issue_title, article.issue_title)

        article.page_numbers='x–ix'
        article.save()
        expected_article_issue_title = 'Volume 5 • Issue 4 • ' \
                                       '2025 • Fall 2025 • x–ix'
        self.assertEqual(expected_article_issue_title, article.issue_title)

        article.first_page = None
        article.last_page = None
        article.page_numbers = None
        article.total_pages = 1
        article.save()
        expected_article_issue_title = 'Volume 5 • Issue 4 • ' \
                                       '2025 • Fall 2025 • 1 page'
        self.assertEqual(expected_article_issue_title, article.issue_title)

    def test_url_based_orcid_cleaned(self):
        clean_orcid = forms.utility_clean_orcid('https://orcid.org/0000-0003-2126-266X')
        self.assertEqual(
            clean_orcid,
            '0000-0003-2126-266X',
        )

    def test_orcid_value_error_raised(self):
        with self.assertRaises(ValueError):
            forms.utility_clean_orcid('Mauro-sfak-orci-dtst')

    def test_author_form_with_bad_orcid(self):
        form = forms.AuthorForm(
            {
                'first_name': 'Mauro',
                'last_name': 'Sanchez',
                'biography': 'Mauro is a Jedi Master hailing from the planet Galicia.',
                'institution': 'Birkbeck, University of London',
                'email': 'mauro@janeway.systems',
                'orcid': 'Mauro-sfak-orci-dtst',
            }
        )
        self.assertFalse(
            form.is_valid(),
        )

    def test_author_form_with_good_orcid(self):
        form = forms.AuthorForm(
            {
                'first_name': 'Andy',
                'last_name': 'Byers',
                'biography': 'Andy is a Jedi Master hailing from the planet Scotland.',
                'institution': 'Birkbeck, University of London',
                'email': 'andy@janeway.systems',
                'orcid': 'https://orcid.org/0000-0003-2126-266X',
            }
        )
        self.assertTrue(
            form.is_valid(),
        )
        self.assertEqual(
            form.cleaned_data.get('orcid'),
            '0000-0003-2126-266X',
        )

    def test_article_encoding_bibtex(self):
        article = helpers.create_article(
            journal=self.journal_one,
            title="Test article: a test article",
            stage="Published",
            abstract="test_abstract",
            date_published=datetime(1990, 1, 1, 12, 00),
        )
        helpers.create_issue(self.journal_one, 2, 1, articles=[article])
        author_a, author_b = self.create_authors()
        logic.add_user_as_author(author_a, article)
        logic.add_user_as_author(author_b, article)

        article.snapshot_authors()
        bibtex = encoding.encode_article_as_bibtex(article)
        expected = """
            @article{TST %s,
                author = {Martin Eve, Mauro Sanchez},
                title = {Test article: a test article},
                volume = {2},
                year = {1990},
                url = {http://localhost/TST/article/id/%s/},
                issue = {1},
                abstract = {test_abstract},
                month = {1},
                issn = {%s},
                publisher={},
                journal = {%s}
            }
        """ % (article.pk, article.pk, article.journal.issn, article.journal.name)
        bibtex_lines = [
            line.strip() for line in bibtex.splitlines() if line.strip()
        ]
        expected_lines = [
            line.strip() for line in expected.splitlines() if line.strip()
        ]
        self.assertEqual(bibtex_lines, expected_lines)

    def test_article_encoding_ris(self):
        article = helpers.create_article(
            journal=self.journal_one,
            title="Test article: A RIS export test case",
            stage="Published",
            abstract="test_abstract",
            date_published=datetime(1990, 1, 1, 12, 00),
        )
        helpers.create_issue(self.journal_one, 2, 2, articles=[article])
        author_a, author_b = self.create_authors()
        logic.add_user_as_author(author_a, article)
        logic.add_user_as_author(author_b, article)

        article.snapshot_authors()
        ris = encoding.encode_article_as_ris(article)
        expected = """
            TY  - JOUR
            AB  - test_abstract
            AU  - Martin Eve, Mauro Sanchez
            DA  - 1990/1//
            IS  - 2
            VL  - 2
            PB  -
            PY  - 1990
            TI  - Test article: A RIS export test case
            T2  - {journal_name}
            UR  - http://localhost/TST/article/id/{article_id}/
            ER  -
        """.format(article_id=article.pk, journal_name=article.journal.name)
        ris_lines = [
            line.strip() for line in ris.splitlines() if line.strip()
        ]
        expected_lines = [
            line.strip() for line in expected.splitlines() if line.strip()
        ]
        self.assertEqual(ris_lines, expected_lines)

    def test_page_range_first_last(self):
        article = models.Article.objects.create(
            journal=self.journal_one,
            title='Test article: A test of page ranges',
            first_page=3,
            last_page=5,
        )
        self.assertEqual(article.page_range, '3–5')

    def test_page_range_first_only(self):
        article = models.Article.objects.create(
            journal=self.journal_one,
            title='Test article: A test of page ranges',
            first_page=3,
        )
        self.assertEqual(article.page_range, '3')

    def test_page_range_custom(self):
        article = models.Article.objects.create(
            journal=self.journal_one,
            title='Test article: A test of page ranges',
            first_page=3,
            last_page=5,
            page_numbers='custom'
        )
        self.assertEqual(article.page_range, 'custom')


class ArticleSearchTests(TransactionTestCase):
    roles_path = os.path.join(
        settings.BASE_DIR,
        'utils',
        'install',
        'roles.json'
    )
    fixtures = [roles_path]

    @staticmethod
    def create_journal():
        """
        Creates a dummy journal for testing
        :return: a journal
        """
        update_xsl_files()
        update_settings()
        journal_one = journal_models.Journal(code="TST", domain="testserver")
        journal_one.title = "Test Journal: A journal of tests"
        journal_one.save()
        update_issue_types(journal_one)

        return journal_one

    @staticmethod
    def create_authors():
        author_1_data = {
            'is_active': True,
            'password': 'this_is_a_password',
            'salutation': 'Prof.',
            'first_name': 'Martin',
            'last_name': 'Eve',
            'department': 'English & Humanities',
            'institution': 'Birkbeck, University of London',
        }
        author_2_data = {
            'is_active': True,
            'password': 'this_is_a_password',
            'salutation': 'Sr.',
            'first_name': 'Mauro',
            'last_name': 'Sanchez',
            'department': 'English & Humanities',
            'institution': 'Birkbeck, University of London',
        }
        author_1 = Account.objects.create(email="1@t.t", **author_1_data)
        author_2 = Account.objects.create(email="2@t.t", **author_1_data)

        return author_1, author_2

    def setUp(self):
        """
        Setup the test environment.
        :return: None
        """
        self.journal_one = self.create_journal()
        self.editor = helpers.create_editor(self.journal_one)
        self.press = helpers.create_press()

    @override_settings(ENABLE_FULL_TEXT_SEARCH=True)
    def test_article_full_text_search(self):
        text_to_search = """
            Exceeding reaction chamber thermal limit.
            We have begun power-supply calibration.
            Force fields have been established on all turbo lifts and crawlways.
            Computer, run a level-two diagnostic on warp-drive systems.
        """
        from django.db import connection
        if connection.vendor == "sqlite":
            # No native support for full text search in sqlite
            return
        needle = "turbo lifts"

        article = models.Article.objects.create(
            journal=self.journal_one,
            title="Testing the search of articles",
            date_published=dateparser.parse("2020-01-01"),
            stage=models.STAGE_PUBLISHED,
        )
        _other_article = models.Article.objects.create(
            journal=self.journal_one,
            title="This article should not appear",
            date_published=dateparser.parse("2020-01-01"),
        )
        file_obj = File.objects.create(article_id=article.pk)
        create_galley(article, file_obj)
        FileText = swapper.load_model("core", "FileText")
        text_to_search = FileText.preprocess_contents(text_to_search)
        text = FileText.objects.create(
            contents=text_to_search,
        )
        file_obj.text = text
        file_obj.save()

        # Mysql can't search at all without FULLTEXT indexes installed
        call_command("generate_search_indexes")

        search_filters = {"full_text": True}
        queryset = models.Article.objects.search(needle, search_filters)
        result = [a for a in queryset]

        self.assertEqual(result, [article])

    @override_settings(ENABLE_FULL_TEXT_SEARCH=True)
    def test_article_search_abstract(self):
        text_to_search = """
            Exceeding reaction chamber thermal limit.
            We have begun power-supply calibration.
            Force fields have been established on all turbo lifts and crawlways.
            Computer, run a level-two diagnostic on warp-drive systems.
        """
        needle = "Crawlways"

        article = models.Article.objects.create(
            journal=self.journal_one,
            title="Test searching abstract",
            date_published=dateparser.parse("2020-01-01"),
            stage=models.STAGE_PUBLISHED,
            abstract=text_to_search,
        )
        other_article = models.Article.objects.create(
            journal=self.journal_one,
            title="This article should not appear",
            date_published=dateparser.parse("2020-01-01"),
            abstract="Random abstract crawl text",
        )

        # Mysql can't search at all without FULLTEXT indexes installed
        call_command("generate_search_indexes")

        search_filters = {"abstract": True}
        queryset = models.Article.objects.search(needle, search_filters)
        result = [a for a in queryset]

        self.assertEqual(result, [article])

    @override_settings(ENABLE_FULL_TEXT_SEARCH=True)
    def test_article_search_title(self):
        text_to_search ="Computer, run a level-two diagnostic on warp-drive systems."
        needle = "diagnostic"

        article = models.Article.objects.create(
            journal=self.journal_one,
            title=text_to_search,
            date_published=dateparser.parse("2020-01-01"),
            stage=models.STAGE_PUBLISHED,
        )
        other_article = models.Article.objects.create(
            journal=self.journal_one,
            title="This article should not appear",
            date_published=dateparser.parse("2020-01-01"),
        )

        # Mysql can't search at all without FULLTEXT indexes installed
        call_command("generate_search_indexes")

        search_filters = {"title": True}
        queryset = models.Article.objects.search(needle, search_filters)
        result = [a for a in queryset]

        self.assertEqual(result, [article])


class FrozenAuthorModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.frozen_author = models.FrozenAuthor.objects.create(
            name_prefix='Dr.',
            first_name='S.',
            middle_name='Bella',
            last_name='Rogers',
            name_suffix='Esq.',
        )

    def test_full_name(self):
        self.assertEqual('Dr. S. Bella Rogers Esq.', self.frozen_author.full_name())
