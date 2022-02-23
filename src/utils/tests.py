__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.test import TestCase, override_settings
from django.utils import timezone
from django.core import mail
from django.contrib.contenttypes.models import ContentType

from utils import merge_settings, transactional_emails
from utils.forms import FakeModelForm, KeywordModelForm
from utils.testing import helpers
from journal import models as journal_models
from review import models as review_models
from submission import models as submission_models
from utils.install import update_xsl_files


class UtilsTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        helpers.create_press()
        helpers.create_journals()
        helpers.create_roles(['reviewer', 'editor', 'author'])

        update_xsl_files()
        cls.journal_one = journal_models.Journal.objects.get(code="TST", domain="testserver")

        cls.regular_user = helpers.create_regular_user()
        cls.second_user = helpers.create_second_user(cls.journal_one)
        cls.editor = helpers.create_editor(cls.journal_one)
        cls.author = helpers.create_author(cls.journal_one)

        cls.review_form = review_models.ReviewForm.objects.create(name="A Form", slug="A Slug", intro="i", thanks="t",
                                                                  journal=cls.journal_one)

        cls.article_under_review = submission_models.Article.objects.create(owner=cls.regular_user,
                                                                            correspondence_author=cls.regular_user,
                                                                            title="A Test Article",
                                                                            abstract="An abstract",
                                                                            stage=submission_models.STAGE_UNDER_REVIEW,
                                                                            journal_id=cls.journal_one.id)

        cls.review_assignment = review_models.ReviewAssignment.objects.create(article=cls.article_under_review,
                                                                              reviewer=cls.second_user,
                                                                              editor=cls.editor,
                                                                              date_due=timezone.now(),
                                                                              form=cls.review_form)

        cls.request = helpers.Request()
        cls.request.journal = cls.journal_one
        cls.request.press = cls.journal_one.press
        cls.request.site_type = cls.journal_one
        cls.request.user = cls.editor
        cls.request.model_content_type = ContentType.objects.get_for_model(cls.request.journal)

        cls.test_message = 'This message is a test for outgoing email, nothing else.'

        cls.base_kwargs = {
            'request': cls.request,
            'user_message_content': cls.test_message,
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

    @override_settings(URL_CONFIG="domain")
    def test_send_review_complete_acknowledgements(self):
        kwargs = dict(**self.base_kwargs)
        kwargs['review_assignment'] = self.review_assignment

        expected_recipient_one = self.review_assignment.reviewer.email
        expected_recipient_two = self.review_assignment.editor.email

        transactional_emails.send_review_complete_acknowledgements(**kwargs)

        self.assertEqual(expected_recipient_one, mail.outbox[0].to[0])
        self.assertEqual(expected_recipient_two, mail.outbox[1].to[0])

    def test_send_article_decision(self):
        kwargs = self.base_kwargs
        kwargs['article'] = self.article_under_review
        kwargs['decision'] = 'accept'

        expected_recipient_one = self.article_under_review.correspondence_author.email

        transactional_emails.send_article_decision(**kwargs)

        self.assertEqual(expected_recipient_one, mail.outbox[0].to[0])

class TestMergeSettings(TestCase):

    def test_recursive_merge(self):
        base = {
                "setting": "value",
                "setting_a": "value_a",
                "setting_list": ["value_a"],
                "setting_dict": {"a": "a", "b": "a"},
        }

        overrides = {
                "setting_a": "value_b",
                "setting_list": ["value_b"],
                "setting_dict": {"b": "b", "c": "c"},
                "other_setting": "value",
        }

        expected = {
                "setting": "value",
                "setting_a": "value_b",
                "setting_list": ["value_a", "value_b"],
                "setting_dict": {"a": "a", "b": "b", "c": "c"},
                "other_setting": "value",
        }
        result = merge_settings(base, overrides)

        self.assertDictEqual(expected, result)

class TestForms(TestCase):

    @classmethod
    def setUpTestData(cls):
        helpers.create_press()
        helpers.create_journals()

        update_xsl_files()
        cls.journal = journal_models.Journal.objects.get(code="TST", domain="testserver")

    def test_fake_model_form(self):

        class FakeTestForm(FakeModelForm):
            class Meta:
                model = journal_models.Journal
                exclude = tuple()

        form = FakeTestForm()

        with self.assertRaises(NotImplementedError):
            form.save()

    def test_keyword_form(self):

        class KeywordTestForm(KeywordModelForm):
            class Meta:
                update_xsl_files()
                model = journal_models.Journal
                fields = ("keywords",)
                exclude = tuple()
        expected = "Expected Keyword"
        data = {
            "keywords": "Keyword, another one, and another one,%s" % expected
        }
        form = KeywordTestForm(data, instance=self.journal)
        form.is_valid()
        journal = form.save()
        self.assertTrue(journal.keywords.filter(word=expected).exists())


    def test_keyword_form_empty_string(self):

        class KeywordTestForm(KeywordModelForm):
            class Meta:
                update_xsl_files()
                model = journal_models.Journal
                fields = ('keywords', )
                exclude = tuple()

        data = {"keywords": ""}
        form = KeywordTestForm(data, instance=self.journal)
        form.is_valid()
        journal = form.save()
        self.assertFalse(journal.keywords.exists())

