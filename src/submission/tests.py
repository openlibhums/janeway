__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django.test import TestCase
from django.core.management import call_command

from submission import forms
from journal import models as journal_models
from utils.install import update_xsl_files


# Create your tests here.
class SubmissionTests(TestCase):

    def test_new_journals_has_submission_configuration(self):
        if not self.journal_one.submissionconfiguration:
            self.fail('Journal does not have a submissionconfiguration object.')

    def test_submit_start_copyright_notice_disable(self):
        forms.ArticleStart(journal=self.journal_one)
        self.journal_one.submissionconfiguration.copyright_notice = False
        self.journal_one.save()

        try:
            forms.ArticleStart(journal=self.journal_one)
        except KeyError:
            self.fail('Key Error found rendering form.')

    @staticmethod
    def create_journal():
        """
        Creates a dummy journal for testing
        :return: a journal
        """
        update_xsl_files()
        journal_one = journal_models.Journal(code="TST", domain="testserver")
        journal_one.save()

        return journal_one

    def setUp(self):
        """
        Setup the test environment.
        :return: None
        """
        self.journal_one = self.create_journal()
        call_command('load_default_settings')
