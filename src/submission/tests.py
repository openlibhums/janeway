__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
from dateutil import parser as dateparser

from django.test import TestCase

from identifiers import logic as id_logic
from identifiers import logic as id_logic
from journal import models as journal_models
from submission import models
from utils.install import update_xsl_files, update_settings


# Create your tests here.
class SubmissionTests(TestCase):

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
            middle_name="M",
            last_name="Sanchez",
        )
        id_logic.generate_crossref_doi_with_pattern(article)

        expected = """
        <p>
         Sanchez, M,
        (2020) “Test article: a test article”,
        <i>Janeway JS</i> 1(1).
        doi: <a href="https://doi.org//TST.1">https://doi.org//TST.1</a></p>
        """
        self.assertHTMLEqual(expected, article.how_to_cite)

