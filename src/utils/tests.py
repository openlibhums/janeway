__copyright__ = "Copyright 2018 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import io
import os

from django.test import TestCase, override_settings
from django.utils import timezone
from django.core import mail
from django.core.management import call_command
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.template.engine import Engine

import mock
from utils import (
    merge_settings,
    models,
    oidc,
    template_override_middleware,
    setting_handler,
    notify,
)

from utils.transactional_emails import *
from utils.forms import FakeModelForm, KeywordModelForm
from utils.logic import generate_sitemap
from utils.testing import helpers
from utils.install import update_xsl_files
from utils.shared import clear_cache
from utils.notify_plugins import notify_email

from journal import models as journal_models
from review import models as review_models
from submission import models as submission_models
from core import models as core_models, include_urls # include_urls so that notify modules load
from copyediting import models as copyediting_models


class UtilsTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        call_command('load_default_settings')
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        helpers.create_roles(['reviewer', 'editor', 'author', 'section-editor'])

        update_xsl_files()
        cls.journal_one = journal_models.Journal.objects.get(code="TST", domain="testserver")

        cls.regular_user = helpers.create_regular_user()
        cls.second_user = helpers.create_second_user(cls.journal_one)
        cls.editor = helpers.create_editor(cls.journal_one)
        cls.editor_two = helpers.create_editor(cls.journal_one, email='editor2@example.com')
        cls.section_editor = helpers.create_section_editor(cls.journal_one)
        cls.author = helpers.create_author(cls.journal_one)
        cls.copyeditor = helpers.create_copyeditor(cls.journal_one)

        setting_handler.save_setting(
            'general',
            'submission_access_request_contact',
            cls.journal_one,
            cls.editor.email,
        )

        cls.submitted_article = helpers.create_article(cls.journal_one)
        cls.submitted_article.authors.add(cls.author)
        cls.submitted_article.correspondence_author = cls.author

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

        cls.access_request = helpers.create_access_request(
            cls.journal_one,
            cls.author,
            'author',
        )

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

        # Setup issues for sitemap testing
        cls.issue_type, created = journal_models.IssueType.objects.get_or_create(
            journal=cls.journal_one,
            code='test_issue_type',
            pretty_name='Test Issue Type',
            custom_plural='Test Issues Type',
        )
        cls.issue_one, created = journal_models.Issue.objects.get_or_create(
            journal=cls.journal_one,
            volume='1',
            issue='1',
            issue_title='V 1 I 1',
            issue_type=cls.issue_type
        )
        cls.section, create = submission_models.Section.objects.get_or_create(
            journal=cls.journal_one,
            name='Test Section',
        )
        cls.article_one, created = submission_models.Article.objects.get_or_create(
            journal=cls.journal_one,
            owner=cls.author,
            title='This is a test article',
            abstract='This is an abstract',
            stage=submission_models.STAGE_PUBLISHED,
            section=cls.section,
            defaults={
                'date_accepted': timezone.now(),
                'date_published': timezone.now(),
            }
        )
        cls.issue_one.articles.add(cls.article_one)


    # Helper function for email subjects
    def get_default_email_subject(self, setting_name, journal=None):
        journal = journal or self.journal_one
        group = 'email_subject'
        subject = setting_handler.get_email_subject_setting(group, setting_name, journal)
        if subject != setting_name:
            # The test shouldn't pass unless the setting or a default was retrieved.
            # The name serves as a backup in production but shouldn't be let through in testing.
            return subject


class SitemapTests(UtilsTests):

    @override_settings(URL_CONFIG="path")
    def test_press_sitemap_generation(self):

        expected_press_sitemap = """<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="/static/common/xslt/sitemap.xsl"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    
    <sitemap>
        <loc>http://localhost/TST/sitemap.xml</loc>
    </sitemap>
    
    <sitemap>
        <loc>http://localhost/TSA/sitemap.xml</loc>
    </sitemap>
    

    
</sitemapindex>"""

        file = io.StringIO()
        generate_sitemap(
            file=file,
            press=self.press,
        )
        self.assertEqual(
            expected_press_sitemap,
            file.getvalue(),
        )

    @override_settings(URL_CONFIG="path")
    def test_journal_sitemap_generation(self):
        expected_journal_sitemap = """<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="/static/common/xslt/sitemap.xsl"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    
    <sitemap>
        <loc>http://localhost/TST/{}_sitemap.xml</loc>
    </sitemap>
    
</sitemapindex>""".format(self.issue_one.pk)
        file = io.StringIO()
        generate_sitemap(
            file=file,
            journal=self.journal_one,
        )
        self.assertEqual(
            expected_journal_sitemap,
            file.getvalue(),
        )

    @override_settings(URL_CONFIG="path")
    def test_issue_sitemap_generation(self):
        expected_issue_sitemap = """<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="/static/common/xslt/sitemap.xsl"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    
    <url>
        <loc>{article_url}</loc>
        <lastmod>{date_published}</lastmod>
        <changefreq>monthly</changefreq>
    </url>
    
</urlset>""".format(
            article_url=self.article_one.url,
            article_id=self.article_one.pk,
            date_published=self.article_one.date_published.strftime("%Y-%m-%d"),
        )
        file = io.StringIO()
        generate_sitemap(
            file=file,
            issue=self.issue_one,
        )
        self.assertEqual(
            expected_issue_sitemap,
            file.getvalue(),
        )


class TransactionalReviewEmailTests(UtilsTests):
    """
    These test cases cover transactional emails sent
    in the review stage.
    """

    def test_send_reviewer_withdrawl_notice(self):
        kwargs = {
            'review_assignment': self.review_assignment,
            'request': self.request,
            'user_message_content': self.test_message,
            'skip': False
        }

        expected_recipient = self.review_assignment.reviewer.email

        send_reviewer_withdrawl_notice(**kwargs)

        self.assertEqual(expected_recipient, mail.outbox[0].to[0])

        subject_setting_name = 'subject_review_withdrawl'
        subject_setting = self.get_default_email_subject(subject_setting_name)
        expected_subject = "[{0}] {1}".format(self.journal_one.code, subject_setting)
        self.assertEqual(expected_subject, mail.outbox[0].subject)


    def test_send_editor_unassigned_notice(self):
        expected_recipient_one = self.review_assignment.editor.email
        send_editor_unassigned_notice(
            request=self.request,
            message=self.test_message,
            assignment=self.review_assignment,
        )

        self.assertEqual(expected_recipient_one, mail.outbox[0].to[0])

        subject_setting_name = 'subject_unassign_editor'
        subject_setting = self.get_default_email_subject(subject_setting_name)
        expected_subject = "[{0}] {1}".format(self.journal_one.code, subject_setting)
        self.assertEqual(expected_subject, mail.outbox[0].subject)


    def test_send_editor_assigned_acknowledgements(self):

        editor_assignment = helpers.create_editor_assignment(
            article=self.article_under_review,
            editor=self.editor_two,
        )
        expected_recipient_one = editor_assignment.editor.email
        kwargs = dict(**self.base_kwargs)
        kwargs['editor_assignment'] = editor_assignment
        kwargs['acknowledgment'] = True
        send_editor_assigned_acknowledgements(**kwargs)

        self.assertEqual(expected_recipient_one, mail.outbox[0].to[0])

        subject_setting_name = 'subject_editor_assignment'
        subject_setting = self.get_default_email_subject(subject_setting_name)
        expected_subject = "[{0}] {1}".format(self.journal_one.code, subject_setting)
        self.assertEqual(expected_subject, mail.outbox[0].subject)


    def test_send_reviewer_requested_acknowledgements(self):
        kwargs = dict(**self.base_kwargs)
        kwargs['review_assignment'] = self.review_assignment

        expected_recipient_one = self.review_assignment.reviewer.email
        send_reviewer_requested_acknowledgements(**kwargs)

        self.assertEqual(expected_recipient_one, mail.outbox[0].to[0])

        subject_setting_name = 'subject_review_assignment'
        subject_setting = self.get_default_email_subject(subject_setting_name)
        expected_subject = "[{0}] {1}".format(self.journal_one.code, subject_setting)
        self.assertEqual(expected_subject, mail.outbox[0].subject)


    def test_send_review_complete_acknowledgements(self):
        kwargs = dict(**self.base_kwargs)
        kwargs['review_assignment'] = self.review_assignment

        send_review_complete_acknowledgements(**kwargs)

        # first email
        expected_recipient_one = self.review_assignment.reviewer.email
        self.assertEqual(expected_recipient_one, mail.outbox[0].to[0])

        subject_setting_name = 'subject_review_complete_reviewer_acknowledgement'
        subject_setting = self.get_default_email_subject(subject_setting_name)
        expected_subject = "[{0}] {1}".format(self.journal_one.code, subject_setting)
        self.assertEqual(expected_subject, mail.outbox[0].subject)

        # second email
        expected_recipient_two = self.review_assignment.editor.email
        self.assertEqual(expected_recipient_two, mail.outbox[1].to[0])

        subject_setting_name = 'subject_review_complete_acknowledgement'
        subject_setting = self.get_default_email_subject(subject_setting_name)
        expected_subject = "[{0}] {1}".format(self.journal_one.code, subject_setting)
        self.assertEqual(expected_subject, mail.outbox[1].subject)


    def test_send_reviewer_accepted_or_decline_acknowledgements(self):
        kwargs = dict(**self.base_kwargs)
        kwargs['review_assignment'] = self.review_assignment

        # reviewer accepted
        kwargs['accepted'] = True
        send_reviewer_accepted_or_decline_acknowledgements(**kwargs)

        # first email
        expected_recipient_one = self.review_assignment.reviewer.email
        self.assertEqual(expected_recipient_one, mail.outbox[0].to[0])

        subject_setting_name = 'subject_review_accept_acknowledgement'
        subject_setting = self.get_default_email_subject(subject_setting_name)
        expected_subject = "[{0}] {1}".format(self.journal_one.code, subject_setting)
        self.assertEqual(expected_subject, mail.outbox[0].subject)

        # second email
        expected_recipient_two = self.review_assignment.editor.email
        self.assertEqual(expected_recipient_two, mail.outbox[1].to[0])

        subject_setting_name = 'subject_reviewer_acknowledgement'
        subject_setting = self.get_default_email_subject(subject_setting_name)
        expected_subject = "[{0}] {1}".format(self.journal_one.code, subject_setting)
        self.assertEqual(expected_subject, mail.outbox[1].subject)


        # reviewer declined
        kwargs['accepted'] = False
        send_reviewer_accepted_or_decline_acknowledgements(**kwargs)

        # first email
        expected_recipient_one = self.review_assignment.reviewer.email
        self.assertEqual(expected_recipient_one, mail.outbox[2].to[0])

        subject_setting_name = 'subject_review_decline_acknowledgement'
        subject_setting = self.get_default_email_subject(subject_setting_name)
        expected_subject = "[{0}] {1}".format(self.journal_one.code, subject_setting)
        self.assertEqual(expected_subject, mail.outbox[2].subject)

        # second email
        expected_recipient_two = self.review_assignment.editor.email
        self.assertEqual(expected_recipient_two, mail.outbox[3].to[0])

        subject_setting_name = 'subject_reviewer_acknowledgement'
        subject_setting = self.get_default_email_subject(subject_setting_name)
        expected_subject = "[{0}] {1}".format(self.journal_one.code, subject_setting)
        self.assertEqual(expected_subject, mail.outbox[3].subject)


    def test_send_submission_acknowledgement(self):
        """
        Tests whether subjects are correct, nothing else.
        Testing recipients would require some cleaning up of
        test data in the setup method.
        """

        kwargs = dict(**self.base_kwargs)
        kwargs['article'] = self.submitted_article

        send_submission_acknowledgement(**kwargs)

        # first email subject
        subject_setting_name = 'subject_submission_acknowledgement'
        subject_setting = self.get_default_email_subject(subject_setting_name)
        expected_subject = "[{0}] {1}".format(self.journal_one.code, subject_setting)
        self.assertEqual(expected_subject, mail.outbox[0].subject)

        # second email subject
        subject_setting_name = 'subject_editor_new_submission'
        subject_setting = self.get_default_email_subject(subject_setting_name)
        expected_subject = "[{0}] {1}".format(self.journal_one.code, subject_setting)
        self.assertEqual(expected_subject, mail.outbox[1].subject)

    def test_send_article_decision(self):
        kwargs = dict(**self.base_kwargs)
        kwargs['article'] = self.article_under_review
        expected_recipient_one = self.article_under_review.correspondence_author.email

        for i, decision in enumerate(['accept', 'decline']): # to be added: 'undecline'
            kwargs['decision'] = decision

            send_article_decision(**kwargs)

            self.assertEqual(expected_recipient_one, mail.outbox[i].to[0])

            subject_setting_name = f'subject_review_decision_{decision}'
            subject_setting = self.get_default_email_subject(subject_setting_name)
            expected_subject = "[{0}] {1}".format(self.journal_one.code, subject_setting)
            self.assertEqual(expected_subject, mail.outbox[i].subject)


    def test_send_revisions_request(self):
        kwargs = dict(**self.base_kwargs)
        kwargs['revision'] = helpers.create_revision_request(
            article = self.article_under_review,
            editor = self.editor,
        )

        send_revisions_request(**kwargs)

        expected_recipient_one = self.article_under_review.correspondence_author.email
        self.assertEqual(expected_recipient_one, mail.outbox[0].to[0])

        subject_setting_name = 'subject_request_revisions'
        subject_setting = self.get_default_email_subject(subject_setting_name)
        expected_subject = "[{0}] {1}".format(self.journal_one.code, subject_setting)
        self.assertEqual(expected_subject, mail.outbox[0].subject)


    def test_send_revisions_complete(self):
        kwargs = dict(**self.base_kwargs)
        kwargs['revision'] = helpers.create_revision_request(
            article = self.article_under_review,
            editor = self.editor,
        )

        send_revisions_complete(**kwargs)

        expected_recipient_one = self.editor.email
        self.assertEqual(expected_recipient_one, mail.outbox[0].to[0])

        subject_setting_name = 'subject_revisions_complete_receipt'
        subject_setting = self.get_default_email_subject(subject_setting_name)
        expected_subject = "[{0}] {1}".format(self.journal_one.code, subject_setting)
        self.assertEqual(expected_subject, mail.outbox[0].subject)


    def test_send_revisions_author_receipt(self):
        kwargs = dict(**self.base_kwargs)
        kwargs['revision'] = helpers.create_revision_request(
            article = self.article_under_review,
            editor = self.editor,
        )

        send_revisions_author_receipt(**kwargs)

        expected_recipient_one = self.article_under_review.correspondence_author.email
        self.assertEqual(expected_recipient_one, mail.outbox[0].to[0])

        subject_setting_name = 'subject_revisions_complete_receipt'
        subject_setting = self.get_default_email_subject(subject_setting_name)
        expected_subject = "[{0}] {1}".format(self.journal_one.code, subject_setting)
        self.assertEqual(expected_subject, mail.outbox[0].subject)


class CopyeditingEmailSubjectTests(UtilsTests):

    """
    This class covers email subjects used in transactional_emails
    with the exception of review emails (covered above) and 
    production and typesetting (not being actively developed)
    """
    def test_copyediting_email_subjects(self):
        for email_function, subject_setting_name in (
            (send_copyedit_assignment, 'subject_copyeditor_assignment_notification'),
            (send_copyedit_updated, 'subject_copyedit_updated'),
            (send_copyedit_deleted, 'subject_copyedit_deleted'),
            (send_copyedit_decision, 'subject_copyediting_decision'),
            (send_copyedit_author_review, 'subject_copyeditor_notify_author'),
            (send_copyedit_complete, 'subject_copyeditor_notify_editor' ),
            (send_copyedit_ack, 'subject_copyeditor_ack' ),
            (send_copyedit_reopen, 'subject_copyeditor_reopen_task' ),
            (send_author_copyedit_complete, 'subject_author_copyedit_complete'),
       ):
            kwargs = dict(**self.base_kwargs)
            kwargs['copyedit_assignment'] = helpers.create_copyedit_assignment(
                article = self.article_under_review,
                copyeditor = self.copyeditor,
                editor = self.editor,
            )
            kwargs['copyedit'] = kwargs['copyedit_assignment']
            kwargs['decision'] = 'test_decision'
            kwargs['article'] = self.article_under_review
            kwargs['author_review'], created = copyediting_models.AuthorReview.objects.get_or_create(
                author=self.author,
                assignment=kwargs['copyedit'],
                notified=True
            )
            email_function(**kwargs)
            subject_setting = self.get_default_email_subject(subject_setting_name)
            expected_subject = "[{0}] {1}".format(self.journal_one.code, subject_setting)
            self.assertEqual(expected_subject, mail.outbox[-1].subject)


class MiscEmailSubjectTests(UtilsTests):

    """
    These test cases cover transactional email subjects outside a workflow stage.
    """

    def test_send_author_publication_notification(self):
        kwargs = dict(**self.base_kwargs)
        kwargs['user_message'] = kwargs['user_message_content']
        kwargs['article'] = self.article_under_review
        kwargs['section_editors'] = [self.section_editor]
        helpers.create_editor_assignment(
            kwargs['article'],
            kwargs['section_editors'][0],
            assignment_type='section-editor',
        )
        kwargs['peer_reviewers'] = [helpers.create_peer_reviewer(self.journal_one)]
        review_assignment = helpers.create_review_assignment(
            journal=self.journal_one,
            article=kwargs['article'],
            reviewer=kwargs['peer_reviewers'][0],
            editor=self.editor,
        )
        review_assignment.is_complete = True
        review_assignment.date_declined = None
        review_assignment.decision = 'yes'
        review_assignment.save()
        send_author_publication_notification(**kwargs)
        subject_setting = self.get_default_email_subject('subject_author_publication')
        expected_subject = "[{0}] {1}".format(self.journal_one.code, subject_setting)
        self.assertEqual(expected_subject, mail.outbox[0].subject)

        subject_setting = self.get_default_email_subject('subject_section_editor_pub_notification')
        expected_subject = "[{0}] {1}".format(self.journal_one.code, subject_setting)
        self.assertEqual(expected_subject, mail.outbox[1].subject)

        subject_setting = self.get_default_email_subject('subject_peer_reviewer_pub_notification')
        expected_subject = "[{0}] {1}".format(self.journal_one.code, subject_setting)
        self.assertEqual(expected_subject, mail.outbox[2].subject)


    def test_send_draft_decison(self):

        kwargs = dict(**self.base_kwargs)
        kwargs['article'] = self.article_under_review
        kwargs['draft'], created = review_models.DecisionDraft.objects.get_or_create(
            article=kwargs['article'],
            editor=self.editor,
            section_editor=self.section_editor,
            message_to_editor='Test Message',
        )
        send_draft_decison(**kwargs)

        subject_setting = self.get_default_email_subject('subject_draft_editor_message')
        expected_subject = "[{0}] {1}".format(self.journal_one.code, subject_setting)
        self.assertEqual(expected_subject, mail.outbox[0].subject)

    def test_send_draft_decision_declined(self):
        kwargs = dict(**self.base_kwargs)
        kwargs['article'] = self.article_under_review
        kwargs['draft_decision'], created = review_models.DecisionDraft.objects.get_or_create(
            article=kwargs['article'],
            editor=self.editor,
            section_editor=self.section_editor,
            message_to_editor='Test Message',
        )
        send_draft_decision_declined(**kwargs)

        subject_setting = self.get_default_email_subject('subject_notify_se_draft_declined')
        expected_subject = "[{0}] {1}".format(self.journal_one.code, subject_setting)
        self.assertEqual(expected_subject, mail.outbox[0].subject)

    def test_access_request_notification(self):
        kwargs = dict(**self.base_kwargs)
        kwargs['access_request'] = self.access_request
        access_request_notification(**kwargs)

        subject_setting = self.get_default_email_subject('subject_submission_access_request_notification')
        expected_subject = "[{0}] {1}".format(self.journal_one.code, subject_setting)
        self.assertEqual(expected_subject, mail.outbox[0].subject)

    def test_access_request_complete(self):
        kwargs = dict(**self.base_kwargs)
        kwargs['access_request'] = self.access_request
        kwargs['decision'] = 'Test Decision'
        access_request_complete(**kwargs)

        subject_setting = self.get_default_email_subject('subject_submission_access_request_complete')
        expected_subject = "[{0}] {1}".format(self.journal_one.code, subject_setting)
        self.assertEqual(expected_subject, mail.outbox[0].subject)


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
                fields = ("code",)
                exclude = tuple()
        expected = "Expected Keyword"
        data = {
            "keywords": "Keyword, another one, and another one,%s" % expected,
            "code": self.journal.code,
        }
        form = KeywordTestForm(data, instance=self.journal)
        valid = form.is_valid()

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


class TestModels(TestCase):

    @classmethod
    def setUpTestData(cls):
        helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.ten_articles = [helpers.create_article(cls.journal_one) for i in range(10)]

    def test_log_entry_bulk_add_simple_entry(self):
        types = 'Submission'
        pks = ','.join([str(article.pk) for article in self.ten_articles])
        description = f"Sending request for article {pks}"
        level = 'Info'
        models.LogEntry.bulk_add_simple_entry(
            types,
            description,
            level,
            self.ten_articles,
        )
        log_entries = models.LogEntry.objects.filter(types='Submission')
        articles = [entry.target for entry in log_entries]
        self.assertEqual(self.ten_articles, articles)


class NotifyEmail(TestCase):

    @classmethod
    def setUpTestData(cls):
        helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.request = mock.Mock()
        cls.request.site_type.name = 'Mock request site type name'
        cls.request.FILES = None

    def test_send_email_reply_to(self):
        args = [
            'subject',
            'to@example.com',
            'html_body',
            self.journal_one,
            self.request,
        ]

        kwargs = {
            'bcc': 'bcc@example.com',
            'cc': 'cc@example.com',
            'replyto': 'replyto@example.com',
        }

        with mock.patch('utils.notify_plugins.notify_email.EmailMultiAlternatives') as msg:
            notify_email.send_email(*args, **kwargs)
            self.assertIn(kwargs['replyto'], msg.call_args.kwargs['reply_to'])


class TestOIDC(TestCase):

    @override_settings(
        OIDC_OP_TOKEN_ENDPOINT='test.janeway.systems/token',
        OIDC_OP_USER_ENDPOINT='test.janeway.systems/user',
        OIDC_OP_JWKS_ENDPOINT='test.janeway.systems/jwks',
        OIDC_RP_CLIENT_ID='test',
        OIDC_RP_CLIENT_SECRET='test',
        OIDC_RP_SIGN_ALGO='RS256',
    )
    def test_create_user(self):
        oidc_auth_backend = oidc.JanewayOIDCAB()
        claims = {
            'given_name': 'Andy',
            'family_name': 'Byers',
            'email': 'andy@janeway.systems',
        }
        user = oidc_auth_backend.create_user(claims=claims)

        self.assertEqual(
            user.email,
            'andy@janeway.systems',
        )
        self.assertEqual(
            user.username,
            'andy@janeway.systems',
        )

    @override_settings(
        OIDC_OP_TOKEN_ENDPOINT='test.janeway.systems/token',
        OIDC_OP_USER_ENDPOINT='test.janeway.systems/user',
        OIDC_OP_JWKS_ENDPOINT='test.janeway.systems/jwks',
        OIDC_RP_CLIENT_ID='test',
        OIDC_RP_CLIENT_SECRET='test',
        OIDC_RP_SIGN_ALGO='RS256',
    )
    def test_update_user(self):
        user = core_models.Account.objects.create(
            first_name='Andy',
            last_name='Byers',
            email='andy@janeway.systems',
        )
        oidc_auth_backend = oidc.JanewayOIDCAB()
        claims = {
            'given_name': 'Andrew',
            'family_name': 'Byers',
            'email': 'andy@janeway.systems',
        }
        oidc_user = oidc_auth_backend.update_user(user, claims=claims)
        self.assertEqual(
            oidc_user.first_name,
            'Andrew',
        )


class TestThemeMiddleware(TestCase):
    def setUp(self):
        self.journal_one, self.journal_two = helpers.create_journals()

    def test_unalatered_themes(self):
        engine = Engine()
        loader = template_override_middleware.Loader(engine)
        dirs = loader.get_theme_dirs()
        self.assertEqual(
            dirs,
            [os.path.join(settings.BASE_DIR, 'themes', settings.INSTALLATION_BASE_THEME, 'templates')]
        )

    def test_journal_dirs_with_theme(self):
        setting_handler.save_setting(
            'general',
            'journal_theme',
            self.journal_one,
            'LCARS',
        )
        # the middleware heavily caches these settings so we need to clear it.
        clear_cache()

        request = helpers.Request()
        request.journal = self.journal_one
        with helpers.request_context(request):
            engine = Engine()
            loader = template_override_middleware.Loader(engine)
            dirs = loader.get_theme_dirs()

            # in this instance INSTALLATION_BASE_THEME and the base_theme setting will match so only one
            # will appear
            self.assertEqual(
                dirs,
                [
                    os.path.join(settings.BASE_DIR, 'themes', 'LCARS', 'templates'),
                    os.path.join(settings.BASE_DIR, 'themes', 'OLH', 'templates')
                ]
            )

    def test_journal_dirs_with_theme_and_base_theme(self):
        setting_handler.save_setting(
            'general',
            'journal_theme',
            self.journal_one,
            'LCARS',
        )
        setting_handler.save_setting(
            'general',
            'journal_base_theme',
            self.journal_one,
            'material',
        )
        # the middleware heavily caches these settings so we need to clear it.
        clear_cache()

        request = helpers.Request()
        request.journal = self.journal_one
        with helpers.request_context(request):
            engine = Engine()
            loader = template_override_middleware.Loader(engine)
            dirs = loader.get_theme_dirs()

            # in this instance all three themes should be in the dirs as they are all
            # different.
            self.assertEqual(
                dirs,
                [
                    os.path.join(settings.BASE_DIR, 'themes', 'LCARS', 'templates'),
                    os.path.join(settings.BASE_DIR, 'themes', 'material', 'templates'),
                    os.path.join(settings.BASE_DIR, 'themes', 'OLH', 'templates')
                ]
            )

class PreprintsUtilsTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.repo_manager1 = helpers.create_user("repo_man@example.com")
        cls.repo_manager2 = helpers.create_user("repo_man2@example.com")
        cls.other_user = helpers.create_user("other@example.com")

        cls.repository, cls.subject = helpers.create_repository(cls.press, [cls.repo_manager1, cls.repo_manager2], [])

        cls.submitted_preprint = helpers.create_preprint(cls.repository, cls.other_user, cls.subject)

        cls.request = helpers.Request()
        cls.request.user = cls.other_user
        cls.request.repository = cls.repository
        cls.request.press = cls.press
        cls.request.site_type = cls.repository
        cls.request.model_content_type = ContentType.objects.get_for_model(cls.request.repository)

class PreprintsTransactionalEmailTests(PreprintsUtilsTests):

    def test_send_submission_notification_all_managers(self):
        kwargs = {
            'request': self.request,
            'preprint': self.submitted_preprint
        }

        preprint_submission(**kwargs)

        # There should be 3 emails sent 1 to author, 2 to managers
        self.assertEqual(len(mail.outbox), 3)

        expected_recipients = [self.repo_manager1.email, self.repo_manager2.email]
        self.assertIn(mail.outbox[1].to[0], expected_recipients)
        self.assertIn(mail.outbox[2].to[0], expected_recipients)

    def test_send_submission_notification_one(self):
        self.repository.submission_notification_recipients.add(self.repo_manager1)
        self.repository.save()

        kwargs = {
            'request': self.request,
            'preprint': self.submitted_preprint
        }

        preprint_submission(**kwargs)

        expected_recipients = [self.repo_manager1.email]

        self.assertEqual(len(expected_recipients), len(mail.outbox[1].to))
        for r in expected_recipients:
            self.assertIn(r, mail.outbox[1].to)




