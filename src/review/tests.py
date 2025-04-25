__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import os

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.conf import settings

from core import models as core_models, files
from journal import models as journal_models
from production import models as production_models
from review import models as review_models, forms, logic
from submission import models as submission_models
from proofing import models as proofing_models
from press import models as press_models
from utils.install import update_xsl_files, update_settings
from utils import setting_handler
from utils.testing import helpers
from utils.shared import clear_cache


# Create your tests here.
class ReviewTests(TestCase):
    def setUp(self):
        self.files = list()

    @override_settings(URL_CONFIG='domain')
    def test_index_view_with_no_questions(self):
        """
        If no questions exist, an appropriate message should be displayed.
        """
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_review_form_can_save(self):
        review_field_text = 'Here is a review of this paper.'
        first_form = forms.GeneratedForm(
            review_assignment=self.review_assignment,
            fields_required=False,
            data={
                str(self.review_form_element.pk): review_field_text,
            }
        )
        first_form.is_valid()
        self.review_assignment.save_review_form(first_form, self.review_assignment)
        second_form = forms.GeneratedForm(
            review_assignment=self.review_assignment,
            fields_required=False,
        )
        self.assertEqual(
            second_form.fields[str(self.review_form_element.pk)].initial,
            review_field_text,
        )

    def test_total_review_count(self):
        self.assertEqual(
            self.article_review_completed.reviewassignment_set.all().count(),
            3,
        )

    def test_completed_reviews_with_decision_count(self):
        self.assertEqual(
            self.article_review_completed.completed_reviews_with_decision.count(),
            1,
        )

    def test_review_assignment_form_valid(self):
        data = {
            'visibility': 'double-blind',
            'form': self.review_form.pk,
            'date_due': '2900-01-01',
            'reviewer': self.second_reviewer.pk,
        }
        form = forms.ReviewAssignmentForm(
            journal=self.journal_one,
            article=self.article_under_review,
            editor=self.editor,
            reviewers=logic.get_reviewer_candidates(self.article_under_review, self.editor),
            data=data,
        )
        self.assertTrue(form.is_valid())

    def test_review_assignment_form_bad_reviewer(self):
        data = {
            'visibility': 'double-blind',
            'form': self.review_form.pk,
            'date_due': '2900-01-01',
            'reviewer': self.regular_user.pk,
        }
        form = forms.ReviewAssignmentForm(
            journal=self.journal_one,
            article=self.article_under_review,
            editor=self.editor,
            reviewers=logic.get_reviewer_candidates(self.article_under_review, self.editor),
            data=data,
        )
        self.assertFalse(form.is_valid())

    def test_reviewer_decision_form_no_decision(self):
        article = helpers.create_article(
            self.journal_one,
            **{'owner': self.regular_user,
               'title': 'Test Article',
               'stage': submission_models.STAGE_UNDER_REVIEW},
        )
        round, c = review_models.ReviewRound.objects.get_or_create(
            article=article,
            round_number=1,
        )

        data = {
            'reviewer': str(self.regular_user.id),
            'form': self.review_form.pk,
            'visibility': 'double-blind',
            'date_due': '2024-03-13',
        }
        form = forms.ReviewAssignmentForm(
            data,
            journal=self.journal_one,
            article=article,
            editor=self.editor,
            reviewers=[],
        )
        assignment = form.save()
        form = forms.ReviewerDecisionForm(
            instance=assignment,
            decision_required=True,
        )

        self.assertIn(
            "<option value=\"\" selected>-----------</option>",
            form.as_p()
        )
        self.assertFalse(form.is_valid())

    def test_csv_reviewer_import_good(self):
        # create a fake request object
        request = self.setup_request_object()

        # prep csv
        csv_content = "{}\n{}".format(
            self.reviewer_csv_header_row,
            self.good_reviewer_content_line,
        )
        self.test_csv = SimpleUploadedFile(
            'test_reviewer_file.csv',
            bytes(csv_content.encode("utf-8"))
        )
        filename, path = files.save_file_to_temp(self.test_csv)

        # prep form with data
        details_form = forms.BulkReviewAssignmentForm(
            {
                'visibility': 'double-blind',
                'form': self.review_form,
                'date_due': '2023-01-01',
            }
        )
        details_form.is_valid()

        reviewers, error = logic.process_reviewer_csv(
            path,
            request,
            self.article_under_review,
            details_form,
        )
        self.assertTrue(
            isinstance(
                reviewers[0].get('review_assignment'),
                review_models.ReviewAssignment,
            )
        )
        self.assertFalse(
            error
        )
        os.unlink(path)

    def test_csv_reviewer_import_bad(self):
        # create a fake request object
        request = self.setup_request_object()
        self.test_csv = SimpleUploadedFile(
            'test_reviewer_file.csv',
            bytes(self.empty_reviewer_content_line)
        )
        filename, path = files.save_file_to_temp(self.test_csv)

        # prep form with data
        details_form = forms.BulkReviewAssignmentForm(
            {
                'visibility': 'double-blind',
                'form': self.review_form,
                'date_due': '2023-01-01',
            }
        )
        details_form.is_valid()
        reviewers, error = logic.process_reviewer_csv(
            path,
            request,
            self.article_under_review,
            details_form,
        )
        self.assertFalse(reviewers)
        os.unlink(path)

    def test_csv_review_import_uses_existing_user_account(self):
        request = self.setup_request_object()

        # prep csv
        csv_content = "{}\n{}".format(
            self.reviewer_csv_header_row,
            self.regular_user_csv_line,
        )
        self.test_csv = SimpleUploadedFile(
            'test_reviewer_file.csv',
            bytes(csv_content.encode("utf-8"))
        )
        filename, path = files.save_file_to_temp(self.test_csv)

        # prep form with data
        details_form = forms.BulkReviewAssignmentForm(
            {
                'visibility': 'double-blind',
                'form': self.review_form,
                'date_due': '2023-01-01',
            }
        )
        details_form.is_valid()
        reviewers, error = logic.process_reviewer_csv(
            path,
            request,
            self.article_under_review,
            details_form,
        )
        self.assertTrue(
            reviewers[0].get('account'),
            self.regular_user,
        )

    def test_csv_doesnt_create_duplicate_assignments(self):
        request = self.setup_request_object()

        # prep csv
        csv_content = "{}\n{}".format(
            self.reviewer_csv_header_row,
            self.regular_user_csv_line,
        )
        self.test_csv = SimpleUploadedFile(
            'test_reviewer_file.csv',
            bytes(csv_content.encode("utf-8"))
        )
        filename, path = files.save_file_to_temp(self.test_csv)

        # prep form with data
        details_form = forms.BulkReviewAssignmentForm(
            {
                'visibility': 'double-blind',
                'form': self.review_form,
                'date_due': '2023-01-01',
            }
        )
        details_form.is_valid()
        reviewers, error = logic.process_reviewer_csv(
            path,
            request,
            self.article_review_completed,
            details_form,
        )
        self.assertTrue(
            reviewers[0].get('review_assignment'),
            self.review_assignment_complete,
        )

    def test_incomplete_reviews(self):
        args = {'owner': self.regular_user,
                'title': 'Test Article',
                'stage': submission_models.STAGE_UNDER_REVIEW,}
        article1 = helpers.create_article(self.journal_one, **args)

        article1.correspondence_author = self.regular_user
        article1.save()

        round =  review_models.ReviewRound.objects.create(article=article1,
                                                          round_number=1,)

        assignment = helpers.create_review_assignment(
                                        journal=self.journal_one,
                                        article=article1,
                                        is_complete=False,
                                        review_round=round,
                                        reviewer=self.regular_user,
                                    )
        assignment.decision = None
        assignment.save()

        self.client.force_login(self.editor)
        decline_url = reverse('review_decision',
                              kwargs={'article_id': article1.pk,
                                      'decision': 'decline'})
        response = self.client.get(decline_url,
                                   SERVER_NAME=self.journal_one.domain,)
        msg = "The following incomplete reviews will be marked as withdrawn"
        self.assertContains(response, msg)

        data = {'cc': [''],
                'bcc': [''],
                'subject': ['Article Declined'],
                'body': ['Article Declined'],
                'attachments': [''],
                'skip': ['skip']}
        response = self.client.post(decline_url,
                                    data,
                                    SERVER_NAME=self.journal_one.domain,)
        review_set = article1.reviewassignment_set.all()
        self.assertEqual(review_set.filter(is_complete=True).count(), 1)
        self.assertEqual(review_set.filter(is_complete=False).count(), 0)

    def test_completed_reviews_shared_setting(self):
        # setup data
        article_with_completed_reviews = helpers.create_article(
            self.journal_one,
            **{'owner': self.regular_user,
                'title': 'Test Article',
                'stage': submission_models.STAGE_UNDER_REVIEW}
        )
        round_one, c = review_models.ReviewRound.objects.get_or_create(
            article=article_with_completed_reviews,
            round_number=1,
        )
        round_two, c = review_models.ReviewRound.objects.get_or_create(
            article=article_with_completed_reviews,
            round_number=2,
        )
        round_one_completed_review = helpers.create_review_assignment(
            journal=self.journal_one,
            article=article_with_completed_reviews,
            is_complete=True,
            review_round=round_one,
        )
        round_two_active_review = helpers.create_review_assignment(
            journal=self.journal_one,
            article=article_with_completed_reviews,
            is_complete=False,
            review_round=round_two,
            reviewer=self.regular_user,
        )

        # turn setting on
        setting_handler.save_setting(
            setting_group_name='general',
            setting_name='display_completed_reviews_in_additional_rounds',
            journal=self.journal_one,
            value='On',
        )
        clear_cache()

        # test on
        self.client.force_login(self.second_user)
        reversed_url = reverse(
                'do_review',
                kwargs={
                    'assignment_id': round_two_active_review.pk,
                }
            )
        url_with_access_code = f"{reversed_url}?access_code={round_two_active_review.access_code}"
        response = self.client.get(
            url_with_access_code,
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertContains(
            response,
            f"View Review #{round_one_completed_review.pk}"
        )

        # turn setting off
        setting_handler.save_setting(
            setting_group_name='general',
            setting_name='display_completed_reviews_in_additional_rounds',
            journal=self.journal_one,
            value='',
        )
        clear_cache()

        # test off
        self.client.force_login(self.regular_user)
        response = self.client.get(
            url_with_access_code,
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertNotContains(
            response,
            "Please click 'View Review' below to view the peer review report"
        )

    def test_shared_review_download_view(self):
        """
        Tests route 1 of the reviewer_shared_review_download view allows and
        denies access as required.
        """
        article_with_completed_reviews = helpers.create_article(
            self.journal_one,
            **{'owner': self.regular_user,
               'title': 'Test Article',
               'stage': submission_models.STAGE_UNDER_REVIEW}
        )
        round_one, c = review_models.ReviewRound.objects.get_or_create(
            article=article_with_completed_reviews,
            round_number=1,
        )
        round_two, c = review_models.ReviewRound.objects.get_or_create(
            article=article_with_completed_reviews,
            round_number=2,
        )
        request = self.setup_request_object()
        test_file = SimpleUploadedFile(
            "file.txt",
            b"content",
        )
        file = files.save_file(
            request,
            test_file,
            label='Test',
            public=True,
            path_parts=('articles', article_with_completed_reviews.pk),
        )
        round_one_completed_review = helpers.create_review_assignment(
            journal=self.journal_one,
            article=article_with_completed_reviews,
            is_complete=True,
            review_round=round_one,
            reviewer=self.second_reviewer,
            review_file=file,
        )
        round_two_active_review = helpers.create_review_assignment(
            journal=self.journal_one,
            article=article_with_completed_reviews,
            is_complete=False,
            review_round=round_two,
            reviewer=self.second_user,
        )

        # turn setting on
        setting_handler.save_setting(
            setting_group_name='general',
            setting_name='display_completed_reviews_in_additional_rounds',
            journal=self.journal_one,
            value='On',
        )
        clear_cache()
        download_url = reverse(
            'reviewer_shared_review_download',
            kwargs={
                'article_id': article_with_completed_reviews.pk,
                'review_id': round_one_completed_review.pk,
            }
        )

        # in this instance, second_user should have access to download the
        self.client.force_login(
            self.second_user,
        )
        response = self.client.get(
            download_url,
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(
            response.status_code,
            200,
        )

        # in this instance second_reviewer should not have any access.
        self.client.force_login(
            self.second_reviewer,
        )
        response = self.client.get(
            download_url,
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEquals(
            response.status_code,
            404,
        )

        # if we now mark this article as shared second_reviewer should
        # be able to access the download
        article_with_completed_reviews.reviews_shared = True
        article_with_completed_reviews.save()

        self.client.force_login(
            self.second_reviewer,
        )
        response = self.client.get(
            download_url,
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEquals(
            response.status_code,
            200,
        )

        # test that a regular user cant access the download link
        self.client.force_login(
            self.regular_user,
        )
        response = self.client.get(
            download_url,
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEquals(
            response.status_code,
            403,
        )

        # finally, delete the file from disk
        files.delete_file(article_with_completed_reviews, file)


    def setup_request_object(self):
        request = helpers.Request()
        request.user = self.editor
        request.journal = self.journal_one
        request.press = self.journal_one.press
        request.site_type = self.journal_one
        return request

    @staticmethod
    def create_user(username, roles=None, journal=None):
        """
        Creates a user with the specified permissions.
        :return: a user with the specified permissions
        """
        # For consistency, outsourced to newer testing helpers
        return helpers.create_user(
            username,
            roles=roles,
            journal=journal,
        )

    @staticmethod
    def create_roles(roles=None):
        """
        Creates the necessary roles for testing.
        :return: None
        """
        # For consistency, outsourced to newer testing helpers
        helpers.create_roles(roles=roles)

    @staticmethod
    def create_journals():
        """
        Creates a set of dummy journals for testing
        :return: a 2-tuple of two journals
        """
        update_settings()
        update_xsl_files()
        journal_one = journal_models.Journal(code="TST", domain="testserver")
        journal_one.save()

        journal_two = journal_models.Journal(code="TSA", domain="journal2.localhost")
        journal_two.save()

        return journal_one, journal_two

    def setUp(self):
        """
        Setup the test environment.
        :return: None
        """
        self.journal_one, self.journal_two = self.create_journals()
        self.create_roles(["editor", "author", "reviewer", "proofreader",
                           "production", "copyeditor", "typesetter",
                           "proofing-manager", "section-editor"])

        self.regular_user = self.create_user("regularuser@martineve.com")
        self.regular_user.is_active = True
        self.regular_user.save()

        self.second_user = self.create_user("seconduser@martineve.com", ["reviewer"], journal=self.journal_one)
        self.second_user.is_active = True
        self.second_user.save()

        self.admin_user = self.create_user("adminuser@martineve.com")
        self.admin_user.is_staff = True
        self.admin_user.is_active = True
        self.admin_user.save()

        self.inactive_user = self.create_user("disableduser@martineve.com", ["editor", "author", "proofreader",
                                                                             "production"], journal=self.journal_one)
        self.inactive_user.is_active = False
        self.inactive_user.save()

        self.editor = self.create_user("editoruser@martineve.com", ["editor"], journal=self.journal_one)
        self.editor.is_active = True
        self.editor.save()

        self.author = self.create_user("authoruser@martineve.com", ["author"], journal=self.journal_one)
        self.author.is_active = True
        self.author.save()

        self.proofreader = self.create_user("proofreader@martineve.com", ["proofreader"], journal=self.journal_one)
        self.proofreader.is_active = True
        self.proofreader.save()

        self.proofreader_two = self.create_user("proofreader2@martineve.com", ["proofreader"], journal=self.journal_one)
        self.proofreader_two.is_active = True
        self.proofreader_two.save()

        self.production = self.create_user("production@martineve.com", ["production"], journal=self.journal_one)
        self.production.is_active = True
        self.production.save()

        self.copyeditor = self.create_user("copyeditor@martineve.com", ["copyeditor"], journal=self.journal_one)
        self.copyeditor.is_active = True
        self.copyeditor.save()

        self.typesetter = self.create_user("typesetter@martineve.com", ["typesetter"], journal=self.journal_one)
        self.typesetter.is_active = True
        self.typesetter.save()

        self.other_typesetter = self.create_user("other_typesetter@martineve.com", ["typesetter"],
                                                 journal=self.journal_one)
        self.other_typesetter.is_active = True
        self.other_typesetter.save()

        self.proofing_manager = self.create_user(
            "proofing_manager@martineve.com",
            ["proofing-manager"],
            journal=self.journal_one
        )
        self.proofing_manager.is_active = True
        self.proofing_manager.save()

        self.other_typesetter.is_active = True
        self.other_typesetter.save()

        self.section_editor = self.create_user("section_editor@martineve.com", ['section-editor'],
                                               journal=self.journal_one)
        self.section_editor.is_active = True
        self.section_editor.save()

        self.second_reviewer = self.create_user("second_reviewer@martineve.com", ['reviewer'],
                                                journal=self.journal_one)
        self.second_reviewer.is_active = True
        self.second_reviewer.save()

        self.public_file = core_models.File(mime_type="A/FILE",
                                            original_filename="blah.txt",
                                            uuid_filename="UUID.txt",
                                            label="A file that is public",
                                            description="Oh yes, it's a file",
                                            owner=self.regular_user,
                                            is_galley=False,
                                            privacy="public")

        self.public_file.save()

        self.private_file = core_models.File(mime_type="A/FILE",
                                             original_filename="blah.txt",
                                             uuid_filename="UUID.txt",
                                             label="A file that is private",
                                             description="Oh yes, it's a file",
                                             owner=self.regular_user,
                                             is_galley=False,
                                             privacy="owner")

        self.private_file.save()

        self.article_in_production = submission_models.Article(owner=self.regular_user, title="A Test Article",
                                                               abstract="An abstract",
                                                               stage=submission_models.STAGE_TYPESETTING,
                                                               journal_id=self.journal_one.id)
        self.article_in_production.save()
        self.article_in_production.data_figure_files.add(self.public_file)

        self.article_unsubmitted = submission_models.Article(owner=self.regular_user, title="A Test Article",
                                                             abstract="An abstract",
                                                             stage=submission_models.STAGE_UNSUBMITTED,
                                                             journal_id=self.journal_one.id)
        self.article_unsubmitted.save()

        self.article_unassigned = submission_models.Article(owner=self.regular_user, title="A Test Article",
                                                            abstract="An abstract",
                                                            stage=submission_models.STAGE_UNASSIGNED,
                                                            journal_id=self.journal_one.id)
        self.article_unassigned.save()

        self.article_assigned = submission_models.Article(owner=self.regular_user, title="A Test Article",
                                                          abstract="An abstract",
                                                          stage=submission_models.STAGE_ASSIGNED,
                                                          journal_id=self.journal_one.id)
        self.article_assigned.save()

        self.article_under_review = submission_models.Article(owner=self.regular_user, title="A Test Article",
                                                              abstract="An abstract",
                                                              stage=submission_models.STAGE_UNDER_REVIEW,
                                                              journal_id=self.journal_one.id)
        self.article_under_review.save()

        self.article_review_completed = submission_models.Article.objects.create(owner=self.regular_user,
                                                                                 title="A Test Article",
                                                                                 abstract="An abstract",
                                                                                 stage=submission_models.STAGE_ACCEPTED,
                                                                                 journal_id=self.journal_one.id,
                                                                                 date_accepted=timezone.now())

        self.article_author_is_owner = submission_models.Article.objects.create(owner=self.author,
                                                                                title="A Test Article",
                                                                                abstract="An abstract",
                                                                                stage=submission_models.STAGE_ACCEPTED,
                                                                                journal_id=self.journal_one.id,
                                                                                date_accepted=timezone.now())

        self.article_author_is_owner.authors.add(self.editor)
        self.article_author_is_owner.authors.add(self.author)

        self.review_form = review_models.ReviewForm(name="A Form", intro="i", thanks="t",
                                                    journal=self.journal_one)
        self.review_form.save()

        self.review_form_element, c = review_models.ReviewFormElement.objects.get_or_create(
            name='Review',
            kind='text',
            order=1,
            required=True,
        )
        self.review_form.elements.add(self.review_form_element)
        self.second_review_form_element, c = review_models.ReviewFormElement.objects.get_or_create(
            name='Second Review Form Element',
            kind='text',
            order=2,
            required=True,
        )
        self.review_form.elements.add(self.second_review_form_element)
        setting_handler.save_setting(
            'general',
            'enable_save_review_progress',
            self.journal_one,
            'On',
        )

        self.round_one = review_models.ReviewRound.objects.create(
            article=self.article_review_completed,
            round_number=1,
        )
        self.round_two = review_models.ReviewRound.objects.create(
            article=self.article_review_completed,
            round_number=2,
        )

        self.review_assignment_complete = review_models.ReviewAssignment(
            article=self.article_review_completed,
            review_round=self.round_one,
            reviewer=self.regular_user,
            editor=self.editor,
            date_due=timezone.now(),
            form=self.review_form,
            is_complete=True,
            date_complete=timezone.now(),
            decision='accept',
        )

        self.review_assignment_complete.save()

        self.review_assignment_withdrawn = review_models.ReviewAssignment.objects.create(
            article=self.article_review_completed,
            review_round=self.round_two,
            reviewer=self.second_reviewer,
            editor=self.editor,
            date_due=timezone.now(),
            form=self.review_form,
            is_complete=True,
            decision='withdrawn',
        )

        self.review_assignment_declined, created = review_models.ReviewAssignment.objects.get_or_create(
            article=self.article_review_completed,
            review_round=self.round_two,
            reviewer=self.second_reviewer,
            editor=self.editor,
            date_due=timezone.now(),
            date_declined=timezone.now(),
            form=self.review_form,
            is_complete=False,
        )

        self.review_assignment = review_models.ReviewAssignment(article=self.article_under_review,
                                                                reviewer=self.second_user,
                                                                editor=self.editor,
                                                                date_due=timezone.now(),
                                                                form=self.review_form)

        self.review_assignment.save()

        self.review_assignment_not_in_scope = review_models.ReviewAssignment(article=self.article_in_production,
                                                                             reviewer=self.regular_user,
                                                                             editor=self.editor,
                                                                             date_due=timezone.now(),
                                                                             form=self.review_form)
        self.review_assignment_not_in_scope.save()

        self.article_under_revision = submission_models.Article(owner=self.regular_user, title="A Test Article",
                                                                abstract="An abstract",
                                                                stage=submission_models.STAGE_UNDER_REVISION,
                                                                journal_id=self.journal_one.id)
        self.article_under_revision.save()

        self.article_rejected = submission_models.Article(owner=self.regular_user, title="A Test Article",
                                                          abstract="An abstract",
                                                          stage=submission_models.STAGE_REJECTED,
                                                          journal_id=self.journal_one.id)
        self.article_rejected.save()

        self.article_accepted = submission_models.Article(owner=self.regular_user, title="A Test Article",
                                                          abstract="An abstract",
                                                          stage=submission_models.STAGE_ACCEPTED,
                                                          journal_id=self.journal_one.id)
        self.article_accepted.save()

        self.section_editor_assignment = review_models.EditorAssignment(article=self.article_assigned,
                                                                        editor=self.section_editor,
                                                                        editor_type='section-editor',
                                                                        notified=True)
        self.section_editor_assignment.save()

        self.article_editor_copyediting = submission_models.Article(owner=self.regular_user, title="A Test Article",
                                                                    abstract="An abstract",
                                                                    stage=submission_models.STAGE_EDITOR_COPYEDITING,
                                                                    journal_id=self.journal_one.id)
        self.article_editor_copyediting.save()

        self.article_author_copyediting = submission_models.Article(owner=self.regular_user, title="A Test Article",
                                                                    abstract="An abstract",
                                                                    stage=submission_models.STAGE_AUTHOR_COPYEDITING,
                                                                    journal_id=self.journal_one.id)
        self.article_author_copyediting.save()

        self.article_final_copyediting = submission_models.Article(owner=self.regular_user, title="A Test Article",
                                                                   abstract="An abstract",
                                                                   stage=submission_models.STAGE_FINAL_COPYEDITING,
                                                                   journal_id=self.journal_one.id)
        self.article_final_copyediting.save()

        self.article_proofing = submission_models.Article(owner=self.regular_user, title="A Test Article",
                                                          abstract="An abstract",
                                                          stage=submission_models.STAGE_PROOFING,
                                                          journal_id=self.journal_one.id)
        self.article_proofing.save()

        assigned = production_models.ProductionAssignment(article=self.article_in_production,
                                                          production_manager=self.production)
        assigned.save()

        self.article_published = submission_models.Article(owner=self.regular_user, title="A Second Test Article",
                                                           abstract="An abstract",
                                                           stage=submission_models.STAGE_PUBLISHED,
                                                           journal_id=self.journal_one.id)
        self.article_published.save()

        assigned = production_models.ProductionAssignment(article=self.article_published,
                                                          production_manager=self.production)
        assigned.save()

        self.article_in_production_inactive = submission_models.Article(owner=self.regular_user, title="A Test Article",
                                                                        abstract="An abstract",
                                                                        stage=submission_models.STAGE_TYPESETTING,
                                                                        journal_id=self.journal_one.id)
        self.article_in_production_inactive.save()

        self.assigned = production_models.ProductionAssignment(article=self.article_in_production_inactive,
                                                               production_manager=self.inactive_user)
        self.assigned.save()

        self.typeset_task = production_models.TypesetTask(assignment=self.assigned,
                                                          typesetter=self.typesetter,
                                                          notified=True,
                                                          accepted=timezone.now())
        self.typeset_task.save()

        self.other_typeset_task = production_models.TypesetTask(assignment=self.assigned,
                                                                typesetter=self.other_typesetter,
                                                                notified=True,
                                                                accepted=timezone.now())
        self.other_typeset_task.save()

        self.proofing_assignment = proofing_models.ProofingAssignment(article=self.article_proofing,
                                                                      proofing_manager=self.proofing_manager,
                                                                      notified=True)
        self.proofing_assignment.save()
        self.proofing_assignment.add_new_proofing_round()

        self.proofing_task = proofing_models.ProofingTask(round=self.proofing_assignment.current_proofing_round(),
                                                          proofreader=self.proofreader,
                                                          notified=True,
                                                          due=timezone.now(),
                                                          accepted=timezone.now(),
                                                          task='sdfsdffs')
        self.proofing_task.save()

        self.correction_task = proofing_models.TypesetterProofingTask(proofing_task=self.proofing_task,
                                                                      typesetter=self.typesetter,
                                                                      notified=True,
                                                                      due=timezone.now(),
                                                                      accepted=timezone.now(),
                                                                      task='fsddsff')
        self.correction_task.save()

        self.journal_one.name = 'Journal One'
        self.journal_two.name = 'Journal Two'
        self.press = press_models.Press.objects.create(name='Press', domain='localhost', main_contact='a@b.com')
        self.press.save()
        update_settings(
            self.journal_one,
            management_command=False,
        )
        self.reviewer_csv_header_row = b"salutation,firstname,middlename,lastname,email_address,department,institution,country,interests,reason"
        self.good_reviewer_content_line = b"Mr,Andy,James,Byers,andy@janeway.systems,Open Library of Humanities,Birkbeck,GB,,Test Reason"
        self.empty_reviewer_content_line = b" "
        self.regular_user_csv_line = b"Mr,Regular,,User,regularuser@martineve.com,Somewhere Dept,Some Inst,GB,,A Reason"

    def test_request_revisions_context(self):
        self.client.force_login(self.editor)
        response = self.client.get(
            reverse(
                'review_request_revisions',
                kwargs={'article_id': self.article_review_completed.pk},
            ),
            SERVER_NAME=self.journal_one.domain,
        )
        response.context.get('incomplete')
        self.assertEqual(
            self.article_review_completed,
            response.context.get('article'),
        )
        # This test does not cover the revision request form
        self.assertEqual(
            0,
            response.context.get('pending_approval').count(),
        )
        self.assertEqual(
            0,
            response.context.get('incomplete').count(),
        )
