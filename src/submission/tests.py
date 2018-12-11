__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django.test import TestCase

from journal import models as journal_models


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
        journal_one = journal_models.Journal(code="TST", domain="testserver")
        journal_one.save()

        return journal_one

    def setUp(self):
        """
        Setup the test environment.
        :return: None
        """
        self.journal_one = self.create_journal()
