__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.test import TestCase
from django.utils import timezone

from utils.testing import setup
from journal import models as journal_models
from review import models as review_models
from submission import models as submission_models


class UtilsTests(TestCase):

    def setUp(self):
        setup.create_press()
        setup.create_journals()
        setup.create_roles()

        self.journal_one = journal_models.Journal.objects.get(code="TST", domain="testserver")

        self.regular_user = setup.create_regular_user()
        self.second_user = setup.create_second_user(self.journal_one)
        self.editor = setup.create_editor(self.journal_one)
        self.author = setup.create_author(self.journal_one)

        self.review_form = review_models.ReviewForm.objects.create(name="A Form", slug="A Slug", intro="i", thanks="t",
                                                                   journal=self.journal_one)

        self.article_under_review = submission_models.Article(owner=self.regular_user, title="A Test Article",
                                                              abstract="An abstract",
                                                              stage=submission_models.STAGE_UNDER_REVIEW,
                                                              journal_id=self.journal_one.id)

        self.review_assignment = review_models.ReviewAssignment(article=self.article_under_review,
                                                                reviewer=self.second_user,
                                                                editor=self.editor,
                                                                date_due=timezone.now(),
                                                                form=self.review_form)

    def test_send_reviewer_withdrawl_notice(self):
        pass
