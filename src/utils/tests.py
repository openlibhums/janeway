__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.test import TestCase
from django.utils import timezone
from django.core import mail
from django.contrib.contenttypes.models import ContentType

from utils.testing import setup
from utils import transactional_emails
from journal import models as journal_models
from review import models as review_models
from submission import models as submission_models


class UtilsTests(TestCase):

    def setUp(self):
        setup.create_press()
        setup.create_journals()
        setup.create_roles(['reviewer', 'editor', 'author'])

        self.journal_one = journal_models.Journal.objects.get(code="TST", domain="testserver")

        self.regular_user = setup.create_regular_user()
        self.second_user = setup.create_second_user(self.journal_one)
        self.editor = setup.create_editor(self.journal_one)
        self.author = setup.create_author(self.journal_one)

        self.review_form = review_models.ReviewForm.objects.create(name="A Form", slug="A Slug", intro="i", thanks="t",
                                                                   journal=self.journal_one)

        self.article_under_review = submission_models.Article.objects.create(owner=self.regular_user,
                                                                             title="A Test Article",
                                                                             abstract="An abstract",
                                                                             stage=submission_models.STAGE_UNDER_REVIEW,
                                                                             journal_id=self.journal_one.id)

        self.review_assignment = review_models.ReviewAssignment.objects.create(article=self.article_under_review,
                                                                               reviewer=self.second_user,
                                                                               editor=self.editor,
                                                                               date_due=timezone.now(),
                                                                               form=self.review_form)

        self.request = setup.Request()
        self.request.journal = self.journal_one
        self.request.site_type = self.journal_one
        self.request.user = self.editor
        self.request.model_content_type = ContentType.objects.get_for_model(self.request.journal)

        self.test_message = 'This message is a test for outgoing email, nothing else.'

        self.base_kwargs = {
            'request': self.request,
            'user_message_content': self.test_message,
            'skip': False,
        }

    def test_send_reviewer_withdrawl_notice(self):
        kwargs = {
            'review_assignment': self.review_assignment,
            'request': self.request,
            'user_message_content': self.test_message,
            'skip': False
        }

        expected_recipient = self.review_assignment.reviewer.email

        transactional_emails.send_reviewer_withdrawl_notice(**kwargs)

        self.assertEqual(expected_recipient, mail.outbox[0].to[0])

    def test_send_review_complete_acknowledgements(self):
        kwargs = self.base_kwargs
        kwargs['review_assignment'] = self.review_assignment

        expected_recipient_one = self.review_assignment.reviewer.email
        expected_recipient_two = self.review_assignment.editor.email

        transactional_emails.send_review_complete_acknowledgements(**kwargs)

        self.assertEqual(expected_recipient_one, mail.outbox[0].to[0])
        self.assertEqual(expected_recipient_two, mail.outbox[1].to[0])
