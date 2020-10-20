__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
from dateutil import parser as dateparser
from mock import Mock

from django.http import Http404
from django.test import TestCase

from core.models import Account
from identifiers import logic as id_logic
from identifiers import logic as id_logic
from journal import models as journal_models
from submission import decorators, models, logic
from utils.install import update_xsl_files, update_settings


# Create your tests here.
class SubmissionTests(TestCase):
    fixtures = ["src/utils/install/roles.json"]

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
        journal_one = journal_models.Journal(code="TST", domain="testserver")
        journal_one.title = "Test Journal: A journal of tests"
        journal_one.save()
        update_settings(journal_one, management_command=False)

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

    def test_article_how_to_cite(self):
        issue = journal_models.Issue.objects.create(journal=self.journal_one)
        journal_models.Issue
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
         Sanchez M. M.,
        (2020) “Test article: a test article”,
        <i>Janeway JS</i> 1(1).
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
