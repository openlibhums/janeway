__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Andy Byers, Mauro Sanchez & Joseph Muller"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.test import Client, TestCase, override_settings
from django.core.exceptions import ValidationError
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.shortcuts import reverse
from django.utils import timezone
from django.core import mail
from django.contrib.messages.storage.cookie import CookieStorage
from django.http import QueryDict
from django.urls.base import clear_script_prefix, set_script_prefix
from django.utils.formats import date_format

from utils.testing import helpers
from utils.install import update_settings
from core import models as cm
from repository import models as rm, install, logic as repository_logic, forms
from freezegun import freeze_time

from dateutil import tz

FROZEN_DATETIME = timezone.datetime(
    2024, 3, 25, 10, 0, tzinfo=tz.gettz("America/Chicago")
)


class TestViews(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.press.save()
        cls.request = helpers.Request()
        cls.request.press = cls.press
        cls.repo_manager = helpers.create_user("repo_manager@janeway.systems")
        cls.repo_manager.is_active = True
        cls.repo_manager.save()
        cls.reviewer = helpers.create_user(
            "repo_reviewer@janeway.systems",
        )
        cls.server_name = "repo.test.com"
        cls.repository, cls.subject = helpers.create_repository(
            cls.press,
            [cls.repo_manager],
            [],
            domain=cls.server_name,
        )
        install.load_settings(cls.repository)
        role = cm.Role.objects.create(name="Reviewer", slug="reviewer")
        rm.RepositoryRole.objects.create(
            repository=cls.repository,
            user=cls.reviewer,
            role=role,
        )
        cls.preprint_author = helpers.create_user(
            username="repo_author@janeway.systems",
        )
        cls.preprint_one = helpers.create_preprint(
            cls.repository,
            cls.preprint_author,
            cls.subject,
            title="Preprint Number One",
        )
        cls.recommendation, _ = rm.ReviewRecommendation.objects.get_or_create(
            repository=cls.repository,
            name="Accept",
        )
        update_settings()

    def setUp(self):
        clear_script_prefix()

    @override_settings(URL_CONFIG="domain")
    def test_invite_reviewer(self):
        data = {
            "reviewer": self.reviewer.pk,
            "date_due": "2022-01-01",
        }
        path = reverse(
            "repository_new_review",
            kwargs={
                "preprint_id": self.preprint_one.pk,
            },
        )
        self.client.force_login(self.repo_manager)
        response = self.client.post(
            path,
            data=data,
            SERVER_NAME=self.server_name,
        )
        self.assertEqual(
            1,
            self.preprint_one.review_set.count(),
        )

    @override_settings(URL_CONFIG="domain")
    def test_notify_reviewer(self):
        review = rm.Review.objects.create(
            reviewer=self.reviewer,
            preprint=self.preprint_one,
            manager=self.repo_manager,
            date_due=timezone.now(),
        )
        data = {
            "message": "This is a test email",
        }
        path = reverse(
            "repository_notify_reviewer",
            kwargs={
                "preprint_id": self.preprint_one.pk,
                "review_id": review.pk,
            },
        )
        self.client.force_login(
            self.repo_manager,
        )
        response = self.client.post(
            path,
            data=data,
            SERVER_NAME=self.server_name,
        )
        self.assertEqual("Preprint Review Invitation", mail.outbox[0].subject)

    @override_settings(URL_CONFIG="domain")
    def test_do_review(self):
        review = rm.Review.objects.create(
            reviewer=self.reviewer,
            preprint=self.preprint_one,
            manager=self.repo_manager,
            date_due=timezone.now(),
            status="new",
        )
        data = {
            "body": "This is my review.",
            "anonymous": True,
            "recommendation": self.recommendation.pk,
        }
        path = reverse(
            "repository_submit_review",
            kwargs={
                "review_id": review.pk,
                "access_code": review.access_code,
            },
        )
        self.client.post(
            path,
            data=data,
            SERVER_NAME=self.server_name,
        )
        comment = rm.Comment.objects.get(
            author=review.reviewer,
            preprint=self.preprint_one,
        )
        self.assertEqual(
            comment.body,
            "This is my review.",
        )

    @override_settings(URL_CONFIG="domain")
    def test_publish_review_comment(self):
        comment = rm.Comment.objects.create(
            author=self.reviewer,
            preprint=self.preprint_one,
            body="This is my review",
        )
        review = rm.Review.objects.create(
            reviewer=self.reviewer,
            preprint=self.preprint_one,
            manager=self.repo_manager,
            date_due=timezone.now(),
            status="complete",
            comment=comment,
        )
        path = reverse(
            "repository_review_detail",
            kwargs={
                "preprint_id": self.preprint_one.pk,
                "review_id": review.pk,
            },
        )
        self.client.force_login(self.repo_manager)
        self.client.post(
            path,
            data={
                "publish": True,
            },
            SERVER_NAME=self.server_name,
        )
        self.assertEqual(
            1,
            self.preprint_one.comment_set.filter(
                review__isnull=False,
                is_public=True,
            ).count(),
        )

    @override_settings(URL_CONFIG="domain")
    def test_unpublish_review_comment(self):
        comment = rm.Comment.objects.create(
            author=self.reviewer,
            preprint=self.preprint_one,
            body="This is my review",
            is_public=True,
            is_reviewed=True,
        )
        review = rm.Review.objects.create(
            reviewer=self.reviewer,
            preprint=self.preprint_one,
            manager=self.repo_manager,
            date_due=timezone.now(),
            status="complete",
            comment=comment,
        )
        path = reverse(
            "repository_review_detail",
            kwargs={
                "preprint_id": self.preprint_one.pk,
                "review_id": review.pk,
            },
        )
        self.client.force_login(self.repo_manager)
        self.client.post(
            path,
            data={
                "unpublish": True,
            },
            SERVER_NAME=self.server_name,
        )
        self.assertEqual(
            0,
            self.preprint_one.comment_set.filter(
                review__isnull=False,
                is_public=True,
            ).count(),
        )

    @override_settings(URL_CONFIG="domain")
    def test_edit_review_comment(self):
        comment = rm.Comment.objects.create(
            author=self.reviewer,
            preprint=self.preprint_one,
            body="This is my review",
            is_public=True,
            is_reviewed=True,
        )
        review = rm.Review.objects.create(
            reviewer=self.reviewer,
            preprint=self.preprint_one,
            manager=self.repo_manager,
            date_due=timezone.now(),
            status="complete",
            comment=comment,
            recommendation=self.recommendation,
        )
        path = reverse(
            "repository_edit_review_comment",
            kwargs={
                "preprint_id": self.preprint_one.pk,
                "review_id": review.pk,
            },
        )
        self.client.force_login(self.repo_manager)
        self.client.post(
            path,
            data={
                "body": "This is my slightly different review.",
                "anonymous": False,
                "recommendation": self.recommendation.pk,
            },
            SERVER_NAME=self.server_name,
        )
        comment = rm.Comment.objects.get(
            author=review.reviewer,
            preprint=self.preprint_one,
        )
        self.assertEqual(
            comment.body,
            "This is my slightly different review.",
        )

    @override_settings(URL_CONFIG="domain")
    @freeze_time(FROZEN_DATETIME)
    def test_accept_preprint(self):
        self.preprint_one.make_new_version(self.preprint_one.submission_file)
        path = reverse(
            "repository_manager_article",
            kwargs={
                "preprint_id": self.preprint_one.pk,
            },
        )
        self.client.force_login(self.repo_manager)
        self.client.post(
            path,
            data={
                "accept": "",
                "datetime": "2024-03-25 10:00",
                "timezone": "America/Chicago",
            },
            SERVER_NAME=self.server_name,
        )
        preprint = rm.Preprint.objects.get(pk=self.preprint_one.pk)
        self.assertEqual(
            preprint.date_published.timestamp(),
            FROZEN_DATETIME.timestamp(),
        )
        self.assertEqual(
            preprint.date_accepted.timestamp(),
            FROZEN_DATETIME.timestamp(),
        )

    @override_settings(URL_CONFIG="domain")
    @freeze_time(FROZEN_DATETIME)
    def test_accept_preprint_with_user_timezone(self):
        # Regression for #3392: when a user's preferred_timezone is set,
        # date_published should be correctly converted to UTC and not end up
        # in the future relative to the server.
        self.preprint_one.make_new_version(self.preprint_one.submission_file)
        path = reverse(
            "repository_manager_article",
            kwargs={"preprint_id": self.preprint_one.pk},
        )
        self.client.force_login(self.repo_manager)
        # User is in Asia/Karachi (UTC+5). FROZEN_DATETIME is 15:00 UTC,
        # so their local time is 20:00. They submit their local time with
        # their correct timezone — date_published should equal FROZEN_DATETIME.
        self.client.post(
            path,
            data={
                "accept": "",
                "datetime": "2024-03-25T20:00",
                "timezone": "Asia/Karachi",
            },
            SERVER_NAME=self.server_name,
        )
        preprint = rm.Preprint.objects.get(pk=self.preprint_one.pk)
        self.assertEqual(
            preprint.date_published.timestamp(),
            FROZEN_DATETIME.timestamp(),
        )

    @override_settings(URL_CONFIG="domain")
    @freeze_time(FROZEN_DATETIME, tz_offset=5)
    def test_accept_preprint_bad_date(self):
        self.preprint_one.make_new_version(self.preprint_one.submission_file)
        path = reverse(
            "repository_manager_article",
            kwargs={
                "preprint_id": self.preprint_one.pk,
            },
        )
        self.client.force_login(self.repo_manager)
        self.client.post(
            path,
            data={
                "accept": "",
                "datetime": "2024-35-35 10:00",
                "timezone": "America/Chicago",
            },
            SERVER_NAME=self.server_name,
        )
        p = rm.Preprint.objects.get(pk=self.preprint_one.pk)
        self.assertIsNone(p.date_published)
        self.assertIsNone(p.date_accepted)

    @override_settings(URL_CONFIG="domain")
    def test_repository_list_renders_with_a_query_string_but_no_search(self):
        for data in [{"theme": "OLH"}, {"subject": self.subject.pk}]:
            with self.subTest(data=data):
                response = self.client.get(
                    reverse("repository_list"),
                    data=data,
                    SERVER_NAME=self.server_name,
                )
                self.assertEqual(response.status_code, 200)

    def test_repo_nav_account_links_do_not_have_return(self):
        """
        Check that the url_with_return tag has *not* been used
        in the site nav links for login and registration.
        """
        for theme in ["clean", "OLH", "material"]:
            data = {
                "theme": theme,
            }
            response = self.client.get(
                "/",
                data=data,
                SERVER_NAME=self.server_name,
            )
            content = response.content.decode()
            self.assertNotIn("/login/?next=", content)
            self.assertNotIn("/register/step/1/?next=", content)

    @override_settings(URL_CONFIG="domain")
    def test_view_preprint_comment_login_link_has_return(self):
        self.preprint_one.make_new_version(self.preprint_one.submission_file)
        self.client.force_login(self.repo_manager)
        post_data = {
            "accept": True,
        }
        manager_url = f"/repository/manager/{self.preprint_one.pk}/"
        self.client.post(
            manager_url,
            data=post_data,
            follow=True,
            SERVER_NAME=self.server_name,
        )
        self.client.logout()

        # Only the material theme has a login URL in
        # src/themes/material/templates/repository/preprint.html
        for theme in ["material"]:
            get_data = {
                "theme": theme,
            }
            view_preprint_url = f"/repository/view/{self.preprint_one.pk}/"
            response = self.client.get(
                view_preprint_url,
                data=get_data,
                SERVER_NAME=self.server_name,
            )
            content = response.content.decode()
            self.assertIn("/login/?next=", content)

    @override_settings(URL_CONFIG="domain")
    def test_journal_search_url_redirects_to_repository_search(self):
        response = self.client.get(
            "/search/",
            SERVER_NAME=self.server_name,
        )
        self.assertRedirects(
            response,
            reverse("repository_search"),
            fetch_redirect_response=False,
        )

    @override_settings(URL_CONFIG="domain")
    def test_journal_search_url_redirects_with_search_term(self):
        response = self.client.get(
            "/search/",
            data={"article_search": "water"},
            SERVER_NAME=self.server_name,
        )
        self.assertRedirects(
            response,
            reverse(
                "repository_search_with_term",
                kwargs={"search_term": "water"},
            ),
            fetch_redirect_response=False,
        )

    @override_settings(URL_CONFIG="domain")
    def test_get_submission_type_or_redirect_missing_type(self):
        request = helpers.Request(repository=self.repository)
        result = repository_logic.get_submission_type_or_redirect(request)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(result.url, reverse("repository_submit"))

    @override_settings(URL_CONFIG="domain")
    def test_get_submission_type_or_redirect_invalid_type(self):
        request = helpers.Request(repository=self.repository)
        request.GET = QueryDict("submission_type=does-not-exist")
        setattr(request, "_messages", CookieStorage(request))
        result = repository_logic.get_submission_type_or_redirect(request)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(result.url, reverse("repository_submit"))

    @override_settings(URL_CONFIG="domain")
    def test_get_submission_type_or_redirect_invalid_ou(self):
        submission_type = rm.RepositorySubmissionType.objects.create(
            repository=self.repository,
            name="Article",
            name_plural="Articles",
            slug="article-invalid-ou",
        )
        request = helpers.Request(repository=self.repository)
        request.GET = QueryDict(
            "submission_type={}&ou=does-not-exist".format(submission_type.slug),
        )
        setattr(request, "_messages", CookieStorage(request))
        result = repository_logic.get_submission_type_or_redirect(request)
        self.assertEqual(result.status_code, 302)
        self.assertEqual(result.url, reverse("repository_submit"))


class TestHierarchyView(TestCase):
    """Tests for the rou_hierarchy_view introduced in iowa-and-isolinear."""

    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.press.save()
        cls.server_name = "hierarchy-test.domain.com"
        cls.repository, cls.subject = helpers.create_repository(
            cls.press, [], [], domain=cls.server_name
        )
        cls.root = rm.RepositoryOrganisationUnit.objects.create(
            repository=cls.repository,
            name="Research",
            code="research",
        )
        cls.child = rm.RepositoryOrganisationUnit.objects.create(
            repository=cls.repository,
            name="Applied",
            code="applied",
            parent=cls.root,
        )
        cls.author = helpers.create_user("hierarchy.author@janeway.systems")
        cls.preprint = helpers.create_preprint(cls.repository, cls.author, cls.subject)
        cls.preprint.stage = rm.STAGE_PREPRINT_PUBLISHED
        cls.preprint.date_published = timezone.now()
        cls.preprint.save()
        cls.preprint.organisation_units.add(cls.root)

    def setUp(self):
        clear_script_prefix()

    @override_settings(URL_CONFIG="domain")
    def test_hierarchy_root_view_returns_200(self):
        """The hierarchy root page (no ROU selected) returns HTTP 200."""
        path = reverse("rou_hierarchy")
        response = self.client.get(path, SERVER_NAME=self.server_name)
        self.assertEqual(response.status_code, 200)

    @override_settings(URL_CONFIG="domain")
    def test_hierarchy_root_view_lists_top_level_rous(self):
        """The root hierarchy page contains the top-level ROU name."""
        path = reverse("rou_hierarchy")
        response = self.client.get(path, SERVER_NAME=self.server_name)
        self.assertContains(response, "Research")

    @override_settings(URL_CONFIG="domain")
    def test_hierarchy_links_to_unit_pages(self):
        """The overview links each unit to its own page."""
        response = self.client.get(
            reverse("rou_hierarchy"),
            SERVER_NAME=self.server_name,
        )
        for unit in (self.root, self.child):
            with self.subTest(unit=unit.code):
                self.assertContains(
                    response,
                    'href="{}"'.format(
                        reverse(
                            "repository_home_by_rou",
                            kwargs={"rou_code": unit.code},
                        )
                    ),
                )

    @override_settings(URL_CONFIG="domain")
    def test_no_separate_hierarchy_page_per_unit(self):
        """Each unit has one page; there is no per-unit hierarchy page."""
        path = "{}{}/".format(reverse("rou_hierarchy"), self.root.code)
        response = self.client.get(path, SERVER_NAME=self.server_name)
        self.assertEqual(response.status_code, 404)

    @override_settings(URL_CONFIG="domain")
    def test_unit_page_shows_preprints(self):
        """A unit's page lists preprints belonging to that unit."""
        path = reverse("repository_home_by_rou", kwargs={"rou_code": self.root.code})
        response = self.client.get(path, SERVER_NAME=self.server_name)
        self.assertContains(response, self.preprint.title)

    @override_settings(URL_CONFIG="domain")
    def test_unknown_unit_code_returns_404(self):
        """A request for a non-existent unit code returns HTTP 404."""
        path = reverse(
            "repository_home_by_rou",
            kwargs={"rou_code": "does-not-exist"},
        )
        response = self.client.get(path, SERVER_NAME=self.server_name)
        self.assertEqual(response.status_code, 404)


class RepositorySubmitWithIdTests(TestCase):
    """Tests for resuming a draft via repository_submit_with_id (#5372)."""

    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.press.save()
        cls.repo_manager = helpers.create_user("repo_manager_5372@janeway.systems")
        cls.repo_manager.is_active = True
        cls.repo_manager.save()
        cls.server_name = "repo5372.test.com"
        cls.repository, cls.subject = helpers.create_repository(
            cls.press,
            [cls.repo_manager],
            [],
            domain=cls.server_name,
        )
        install.load_settings(cls.repository)
        cls.submission_type = rm.RepositorySubmissionType.objects.create(
            repository=cls.repository,
            name="Article",
            name_plural="Articles",
            slug="article-5372",
        )
        cls.draft = rm.Preprint.objects.create(
            repository=cls.repository,
            owner=cls.repo_manager,
            stage=rm.STAGE_PREPRINT_UNSUBMITTED,
            title="Draft preprint 5372",
            abstract="Draft abstract",
            submission_type=cls.submission_type,
        )
        cls.typeless_draft = rm.Preprint.objects.create(
            repository=cls.repository,
            owner=cls.repo_manager,
            stage=rm.STAGE_PREPRINT_UNSUBMITTED,
            title="Typeless draft 5372",
            abstract="Draft abstract",
            submission_type=None,
        )

    def setUp(self):
        clear_script_prefix()

    @override_settings(URL_CONFIG="domain")
    def test_submit_with_id_resumes_draft_without_querystring(self):
        # The URL previously routed to repository_submit, which no longer
        # accepts preprint_id, raising TypeError. It now resolves to
        # repository_info and resumes the draft using its stored type,
        # even though no submission_type is present in the query string.
        self.client.force_login(self.repo_manager)
        response = self.client.get(
            reverse(
                "repository_submit_with_id",
                kwargs={"preprint_id": self.draft.pk},
            ),
            SERVER_NAME=self.server_name,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Draft preprint 5372")

    @override_settings(URL_CONFIG="domain")
    def test_submit_with_id_redirects_when_draft_has_no_type(self):
        # A draft whose submission_type is null cannot be resumed from its
        # stored type, so it falls back to get_submission_type_or_redirect.
        # With no submission_type in the query string this redirects to the
        # start page. This documents the deliberate graceful degradation.
        self.client.force_login(self.repo_manager)
        response = self.client.get(
            reverse(
                "repository_submit_with_id",
                kwargs={"preprint_id": self.typeless_draft.pk},
            ),
            SERVER_NAME=self.server_name,
        )
        self.assertRedirects(
            response,
            reverse("repository_submit"),
            fetch_redirect_response=False,
        )


class RepositoryDashboardDateSubmittedTests(TestCase):
    """The dashboard's Date Submitted column shows the date, not the type (#5441)."""

    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.press.save()
        cls.author = helpers.create_user("repo_author_5441@janeway.systems")
        cls.author.is_active = True
        cls.author.save()
        cls.server_name = "repo5441.test.com"
        cls.repository, cls.subject = helpers.create_repository(
            cls.press,
            [cls.author],
            [],
            domain=cls.server_name,
        )
        install.load_settings(cls.repository)
        cls.submission_type = rm.RepositorySubmissionType.objects.create(
            repository=cls.repository,
            name="Type5441Unique",
            name_plural="Type5441Uniques",
            slug="type-5441-unique",
        )
        cls.preprint = helpers.create_preprint(
            cls.repository,
            cls.author,
            cls.subject,
            title="Dashboard Preprint 5441",
        )
        cls.preprint.submission_type = cls.submission_type
        cls.preprint.save()

    def setUp(self):
        clear_script_prefix()
        self.client = Client()
        self.client.force_login(self.author)

    @override_settings(URL_CONFIG="domain")
    def test_date_submitted_column_shows_the_date(self):
        response = self.client.get(
            reverse("repository_dashboard"),
            SERVER_NAME=self.server_name,
        )
        expected_date = date_format(
            timezone.localtime(self.preprint.date_submitted),
            "DATETIME_FORMAT",
        )
        self.assertContains(response, expected_date)

    @override_settings(URL_CONFIG="domain")
    def test_type_appears_only_in_the_type_column(self):
        response = self.client.get(
            reverse("repository_dashboard"),
            SERVER_NAME=self.server_name,
        )
        self.assertContains(response, self.submission_type.name, count=1)


class TestIdentifierManagementSetting(TestCase):
    """Tests for the Repository.identifier_management setting."""

    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.press.save()
        cls.repo_manager = helpers.create_user("repo_manager_idm@janeway.systems")
        cls.repo_manager.is_active = True
        cls.repo_manager.save()
        cls.server_name = "repoidm.test.com"
        cls.repository, cls.subject = helpers.create_repository(
            cls.press,
            [cls.repo_manager],
            [],
            domain=cls.server_name,
        )
        install.load_settings(cls.repository)
        cls.preprint_author = helpers.create_user(
            username="repo_author_idm@janeway.systems",
        )
        cls.preprint_author.is_active = True
        cls.preprint_author.save()
        cls.staff_member = helpers.create_user(
            username="repo_staff_idm@janeway.systems",
            is_active=True,
            is_staff=True,
        )
        cls.preprint = helpers.create_preprint(
            cls.repository,
            cls.preprint_author,
            cls.subject,
            title="Identifier Management Test Preprint",
        )
        update_settings()

    def setUp(self):
        clear_script_prefix()

    @override_settings(URL_CONFIG="domain")
    def test_manage_identifiers_link_shown_when_setting_on(self):
        self.client.force_login(self.repo_manager)
        response = self.client.get(
            reverse(
                "repository_manager_article",
                kwargs={"preprint_id": self.preprint.pk},
            ),
            SERVER_NAME=self.server_name,
        )
        self.assertContains(response, "Manage Identifiers")

    @override_settings(URL_CONFIG="domain")
    def test_manage_identifiers_link_hidden_when_setting_off(self):
        self.repository.identifier_management = False
        self.repository.save()
        self.client.force_login(self.repo_manager)
        response = self.client.get(
            reverse(
                "repository_manager_article",
                kwargs={"preprint_id": self.preprint.pk},
            ),
            SERVER_NAME=self.server_name,
        )
        self.assertNotContains(response, "Manage Identifiers")

    @override_settings(URL_CONFIG="domain")
    def test_identifiers_view_accessible_when_setting_on(self):
        self.client.force_login(self.repo_manager)
        response = self.client.get(
            reverse(
                "identifiers",
                kwargs={"content_type": "preprint", "object_id": self.preprint.pk},
            ),
            SERVER_NAME=self.server_name,
        )
        self.assertEqual(response.status_code, 200)

    @override_settings(URL_CONFIG="domain")
    def test_identifiers_view_404_when_setting_off(self):
        self.repository.identifier_management = False
        self.repository.save()
        self.client.force_login(self.repo_manager)
        response = self.client.get(
            reverse(
                "identifiers",
                kwargs={"content_type": "preprint", "object_id": self.preprint.pk},
            ),
            SERVER_NAME=self.server_name,
        )
        self.assertEqual(response.status_code, 404)

    @override_settings(URL_CONFIG="domain")
    def test_identifiers_view_denied_for_non_manager(self):
        self.client.force_login(self.preprint_author)
        response = self.client.get(
            reverse(
                "identifiers",
                kwargs={"content_type": "preprint", "object_id": self.preprint.pk},
            ),
            SERVER_NAME=self.server_name,
        )
        self.assertEqual(response.status_code, 403)

    @override_settings(URL_CONFIG="domain")
    def test_add_identifier_view_404_when_setting_off(self):
        self.repository.identifier_management = False
        self.repository.save()
        self.client.force_login(self.repo_manager)
        response = self.client.get(
            reverse(
                "add_new_identifier",
                kwargs={"content_type": "preprint", "object_id": self.preprint.pk},
            ),
            SERVER_NAME=self.server_name,
        )
        self.assertEqual(response.status_code, 404)

    @override_settings(URL_CONFIG="domain")
    def test_identifiers_view_404_for_staff_when_setting_off(self):
        # The setting gates access regardless of user privilege.
        self.repository.identifier_management = False
        self.repository.save()
        self.client.force_login(self.staff_member)
        response = self.client.get(
            reverse(
                "identifiers",
                kwargs={"content_type": "preprint", "object_id": self.preprint.pk},
            ),
            SERVER_NAME=self.server_name,
        )
        self.assertEqual(response.status_code, 404)


class RepositoryFieldTypeScopingTests(TestCase):
    """The field form only offers this repository's submission types (#5440)."""

    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.press.save()
        cls.repo_manager = helpers.create_user("repo_manager_5440@janeway.systems")
        cls.repo_manager.is_active = True
        cls.repo_manager.save()
        cls.server_name = "repo5440.test.com"
        cls.repository, cls.subject = helpers.create_repository(
            cls.press,
            [cls.repo_manager],
            [],
            domain=cls.server_name,
        )
        install.load_settings(cls.repository)
        cls.other_repository, cls.other_subject = helpers.create_repository(
            cls.press,
            [cls.repo_manager],
            [],
            domain="repo5440other.test.com",
        )
        install.load_settings(cls.other_repository)
        cls.local_type = rm.RepositorySubmissionType.objects.create(
            repository=cls.repository,
            name="Local Type 5440",
            name_plural="Local Types 5440",
            slug="local-type-5440",
        )
        cls.foreign_type = rm.RepositorySubmissionType.objects.create(
            repository=cls.other_repository,
            name="Foreign Type 5440",
            name_plural="Foreign Types 5440",
            slug="foreign-type-5440",
        )

    def setUp(self):
        clear_script_prefix()
        self.client = Client()
        self.client.force_login(self.repo_manager)

    @override_settings(URL_CONFIG="domain")
    def test_field_form_offers_only_this_repositorys_types(self):
        response = self.client.get(
            reverse("repository_fields"),
            SERVER_NAME=self.server_name,
        )
        self.assertContains(response, self.local_type.name)
        self.assertNotContains(response, self.foreign_type.name)

    @override_settings(URL_CONFIG="domain")
    def test_field_form_rejects_another_repositorys_type(self):
        self.client.post(
            reverse("repository_fields"),
            {
                "name": "Field 5440",
                "input_type": "text",
                "order": 1,
                "submission_type": self.foreign_type.pk,
            },
            SERVER_NAME=self.server_name,
        )
        self.assertFalse(rm.RepositoryField.objects.filter(name="Field 5440").exists())

    @override_settings(URL_CONFIG="domain")
    def test_field_form_accepts_this_repositorys_type(self):
        self.client.post(
            reverse("repository_fields"),
            {
                "name": "Scoped Field 5440",
                "input_type": "text",
                "order": 1,
                "submission_type": self.local_type.pk,
            },
            SERVER_NAME=self.server_name,
        )
        field = rm.RepositoryField.objects.get(name="Scoped Field 5440")
        self.assertEqual(field.submission_type, self.local_type)
        self.assertEqual(field.repository, self.repository)


class OrganisationUnitTests(TestCase):
    """Back office management and navigation of organisational units."""

    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.press.save()
        cls.repo_manager = helpers.create_user("rou_manager@janeway.systems")
        cls.repo_manager.is_active = True
        cls.repo_manager.save()
        cls.server_name = "rou.test.com"
        cls.repository, cls.subject = helpers.create_repository(
            cls.press,
            [cls.repo_manager],
            [],
            domain=cls.server_name,
        )
        install.load_settings(cls.repository)
        cls.faculty = rm.RepositoryOrganisationUnit.objects.create(
            repository=cls.repository,
            name="Faculty of Arts",
            code="arts",
        )
        cls.department = rm.RepositoryOrganisationUnit.objects.create(
            repository=cls.repository,
            name="History Department",
            code="history",
            parent=cls.faculty,
        )

    def setUp(self):
        clear_script_prefix()

    @override_settings(URL_CONFIG="domain")
    def test_manager_can_add_unit(self):
        self.client.force_login(self.repo_manager)
        self.client.post(
            reverse("repository_organisation_units"),
            data={"name": "Classics", "code": "classics", "parent": self.faculty.pk},
            SERVER_NAME=self.server_name,
        )
        unit = rm.RepositoryOrganisationUnit.objects.get(code="classics")
        self.assertEqual(unit.repository, self.repository)
        self.assertEqual(unit.parent, self.faculty)

    @override_settings(URL_CONFIG="domain")
    def test_manager_can_update_settings(self):
        self.client.force_login(self.repo_manager)
        self.client.post(
            reverse("repository_organisation_units"),
            data={
                "save_settings": "",
                "rou_default_name": "Departments",
                "rou_struct_page_text": "<p>Our departments.</p>",
            },
            SERVER_NAME=self.server_name,
        )
        self.repository.refresh_from_db()
        self.assertEqual(self.repository.rou_default_name, "Departments")

    @override_settings(URL_CONFIG="domain")
    def test_manager_can_delete_unit(self):
        self.client.force_login(self.repo_manager)
        self.client.post(
            reverse("repository_delete_organisation_unit"),
            data={"delete": self.department.pk},
            SERVER_NAME=self.server_name,
        )
        self.assertFalse(
            rm.RepositoryOrganisationUnit.objects.filter(
                pk=self.department.pk,
            ).exists()
        )

    @override_settings(URL_CONFIG="domain")
    def test_reserved_code_rejected(self):
        self.client.force_login(self.repo_manager)
        response = self.client.post(
            reverse("repository_organisation_units"),
            data={"name": "About Us", "code": "about"},
            SERVER_NAME=self.server_name,
        )
        self.assertTrue(response.context["form"].errors.get("code"))
        self.assertFalse(
            rm.RepositoryOrganisationUnit.objects.filter(code="about").exists()
        )

    def test_code_validation_with_path_prefix(self):
        """Path mode sites have a script prefix; it must not affect the check."""
        set_script_prefix(f"/{self.repository.short_name}/")
        self.addCleanup(clear_script_prefix)
        valid = forms.OrganisationUnitForm(
            data={"name": "Classics", "code": "classics"},
            repository=self.repository,
        )
        reserved = forms.OrganisationUnitForm(
            data={"name": "About Us", "code": "about"},
            repository=self.repository,
        )
        self.assertTrue(valid.is_valid(), valid.errors)
        self.assertIn("code", reserved.errors)

    @override_settings(URL_CONFIG="domain")
    def test_duplicate_code_rejected(self):
        self.client.force_login(self.repo_manager)
        response = self.client.post(
            reverse("repository_organisation_units"),
            data={"name": "Art History", "code": "arts"},
            SERVER_NAME=self.server_name,
        )
        self.assertTrue(response.context["form"].errors.get("code"))

    @override_settings(URL_CONFIG="domain")
    def test_unit_cannot_be_moved_under_its_descendant(self):
        self.client.force_login(self.repo_manager)
        response = self.client.get(
            reverse(
                "repository_organisation_units_with_id",
                kwargs={"unit_id": self.faculty.pk},
            ),
            SERVER_NAME=self.server_name,
        )
        parents = response.context["form"].fields["parent"].queryset
        self.assertNotIn(self.faculty, parents)
        self.assertNotIn(self.department, parents)

    @override_settings(URL_CONFIG="domain")
    def test_anonymous_user_cannot_manage_units(self):
        response = self.client.get(
            reverse("repository_organisation_units"),
            SERVER_NAME=self.server_name,
        )
        self.assertNotEqual(response.status_code, 200)

    @override_settings(URL_CONFIG="domain")
    def test_unit_page_links_up_to_parent(self):
        path = reverse(
            "repository_home_by_rou",
            kwargs={"rou_code": self.department.code},
        )
        parent_path = reverse(
            "repository_home_by_rou",
            kwargs={"rou_code": self.faculty.code},
        )
        for theme in ("OLH", "clarity", "material"):
            with self.subTest(theme=theme):
                response = self.client.get(
                    path,
                    {"theme": theme},
                    SERVER_NAME=self.server_name,
                )
                self.assertContains(response, f'href="{parent_path}"')
                self.assertContains(response, 'aria-current="page"')

    @override_settings(URL_CONFIG="domain")
    def test_hierarchy_page_name_is_not_double_pluralised(self):
        for theme in ("OLH", "clarity", "material"):
            with self.subTest(theme=theme):
                response = self.client.get(
                    reverse("rou_hierarchy"),
                    {"theme": theme},
                    SERVER_NAME=self.server_name,
                )
                self.assertContains(response, "Organisational Units")
                self.assertNotContains(response, "Organisational Unitss")

    @override_settings(URL_CONFIG="domain")
    def test_nav_links_to_hierarchy_when_units_exist(self):
        hierarchy_path = reverse("rou_hierarchy")
        for theme in ("OLH", "clarity", "material"):
            with self.subTest(theme=theme):
                response = self.client.get(
                    reverse("repository_about"),
                    {"theme": theme},
                    SERVER_NAME=self.server_name,
                )
                self.assertContains(response, f'href="{hierarchy_path}"')

    @override_settings(URL_CONFIG="domain")
    def test_unit_preprint_list_links_up_to_unit(self):
        path = reverse(
            "repository_preprints_by_rou",
            kwargs={"rou_code": self.department.code},
        )
        unit_path = reverse(
            "repository_home_by_rou",
            kwargs={"rou_code": self.department.code},
        )
        for theme in ("OLH", "clarity", "material"):
            with self.subTest(theme=theme):
                response = self.client.get(
                    path,
                    {"theme": theme},
                    SERVER_NAME=self.server_name,
                )
                self.assertContains(response, f'href="{unit_path}"')

    @override_settings(URL_CONFIG="domain")
    def test_home_lists_top_level_units(self):
        unit_path = reverse(
            "repository_home_by_rou",
            kwargs={"rou_code": self.faculty.code},
        )
        for theme in ("OLH", "clarity", "material"):
            with self.subTest(theme=theme):
                response = self.client.get(
                    reverse("website_index"),
                    {"theme": theme},
                    SERVER_NAME=self.server_name,
                )
                self.assertContains(response, f'href="{unit_path}"')

    @override_settings(URL_CONFIG="domain")
    def test_manager_can_disable_units(self):
        self.client.force_login(self.repo_manager)
        self.client.post(
            reverse("repository_organisation_units"),
            data={
                "save_settings": "",
                "rou_default_name": "Organisational Units",
                "rou_struct_page_text": "",
            },
            SERVER_NAME=self.server_name,
        )
        self.repository.refresh_from_db()
        self.assertFalse(self.repository.enable_organisation_units)
        # Units and their links are kept, only hidden.
        self.assertTrue(
            rm.RepositoryOrganisationUnit.objects.filter(
                pk=self.department.pk,
            ).exists()
        )

    @override_settings(URL_CONFIG="domain")
    def test_page_text_is_not_run_as_a_template(self):
        self.repository.rou_struct_page_text = (
            "<p>{{ repository.name }} {{ repository.managers.all.0.email }} "
            "{% bad tag %}</p>"
        )
        self.repository.save()
        response = self.client.get(
            reverse("rou_hierarchy"),
            SERVER_NAME=self.server_name,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.repository.name)
        self.assertContains(response, "{{ repository.managers.all.0.email }}")
        self.assertNotContains(response, self.repo_manager.email)

    @override_settings(URL_CONFIG="domain")
    def test_hierarchy_counts_only_published_preprints(self):
        author = helpers.create_user("rou_author@janeway.systems")
        published = helpers.create_preprint(
            self.repository,
            author,
            self.subject,
            title="Published unit preprint",
        )
        published.stage = rm.STAGE_PREPRINT_PUBLISHED
        published.date_published = timezone.now() - timezone.timedelta(days=1)
        published.save()
        draft = helpers.create_preprint(
            self.repository,
            author,
            self.subject,
            title="Draft unit preprint",
        )
        draft.stage = rm.STAGE_PREPRINT_UNSUBMITTED
        draft.save()
        for preprint in (published, draft):
            preprint.organisation_units.add(self.department)

        response = self.client.get(
            reverse("rou_hierarchy"),
            SERVER_NAME=self.server_name,
        )
        (faculty,) = response.context["hierarchy"]
        (department,) = faculty["children"]
        self.assertEqual(department["unit"], self.department)
        self.assertEqual(department["preprint_count"], 1)

    @override_settings(URL_CONFIG="domain")
    def test_invalid_settings_do_not_change_displayed_settings(self):
        self.client.force_login(self.repo_manager)
        response = self.client.post(
            reverse("repository_organisation_units"),
            data={
                "save_settings": "",
                "rou_default_name": "",
                "rou_struct_page_text": "",
            },
            SERVER_NAME=self.server_name,
        )
        self.assertTrue(response.context["settings_form"].errors)
        self.assertEqual(
            response.wsgi_request.repository.rou_default_name,
            "Organisational Units",
        )
        self.assertTrue(response.wsgi_request.repository.enable_organisation_units)

    @override_settings(URL_CONFIG="domain")
    def test_non_numeric_unit_ids_return_404(self):
        self.client.force_login(self.repo_manager)
        get_response = self.client.get(
            reverse("repository_organisation_units"),
            {"parent": "abc"},
            SERVER_NAME=self.server_name,
        )
        post_response = self.client.post(
            reverse("repository_delete_organisation_unit"),
            data={"delete": "abc"},
            SERVER_NAME=self.server_name,
        )
        self.assertEqual(get_response.status_code, 404)
        self.assertEqual(post_response.status_code, 404)

    @override_settings(URL_CONFIG="domain")
    def test_hierarchy_counts_use_object_name(self):
        for theme in ("OLH", "clarity", "material"):
            with self.subTest(theme=theme):
                response = self.client.get(
                    reverse("rou_hierarchy"),
                    {"theme": theme},
                    SERVER_NAME=self.server_name,
                )
                self.assertContains(response, "0 Preprints")
                self.assertNotContains(response, "submissions)")


@override_settings(URL_CONFIG="domain")
class DisabledOrganisationUnitTests(TestCase):
    """With organisational units turned off they are hidden but kept."""

    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.press.save()
        cls.server_name = "rou-off.test.com"
        cls.repository, cls.subject = helpers.create_repository(
            cls.press,
            [],
            [],
            domain=cls.server_name,
        )
        install.load_settings(cls.repository)
        cls.repository.enable_organisation_units = False
        cls.repository.save()
        cls.unit = rm.RepositoryOrganisationUnit.objects.create(
            repository=cls.repository,
            name="Faculty of Arts",
            code="arts",
        )

    def setUp(self):
        clear_script_prefix()

    def get(self, path, **params):
        return self.client.get(path, params, SERVER_NAME=self.server_name)

    def test_public_unit_pages_return_404(self):
        paths = [
            reverse("rou_hierarchy"),
            reverse("repository_home_by_rou", kwargs={"rou_code": self.unit.code}),
            reverse(
                "repository_preprints_by_rou",
                kwargs={"rou_code": self.unit.code},
            ),
        ]
        for path in paths:
            with self.subTest(path=path):
                self.assertEqual(self.get(path).status_code, 404)

    def test_units_hidden_on_homepage_and_nav(self):
        unit_path = reverse(
            "repository_home_by_rou",
            kwargs={"rou_code": self.unit.code},
        )
        hierarchy_path = reverse("rou_hierarchy")
        for theme in ("OLH", "clarity", "material"):
            with self.subTest(theme=theme):
                response = self.get(reverse("website_index"), theme=theme)
                self.assertEqual(response.status_code, 200)
                self.assertNotContains(response, f'href="{unit_path}"')
                self.assertNotContains(response, f'href="{hierarchy_path}"')

    def test_submission_start_form_has_no_unit_field(self):
        form = forms.PreSubmissionStartForm(repository=self.repository)
        self.assertNotIn("organisation_unit", form.fields)

    def test_submission_ignores_unit_parameter(self):
        submission_type = rm.RepositorySubmissionType.objects.create(
            repository=self.repository,
            name="Article",
            name_plural="Articles",
            slug="rou-off-article",
        )
        request = helpers.Request()
        request.repository = self.repository
        request.GET = {"submission_type": submission_type.slug, "ou": "arts"}
        result = repository_logic.get_submission_type_or_redirect(request)
        self.assertEqual(result, submission_type)
        self.assertIsNone(request.organisation_unit)


class ClarityRepositoryLogoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.press.save()
        cls.server_name = "repo5615.test.com"
        cls.repository, _ = helpers.create_repository(
            cls.press, [], [], domain=cls.server_name
        )

    def setUp(self):
        clear_script_prefix()

    def get_home(self):
        return self.client.get(
            reverse("website_index"),
            {"theme": "clarity"},
            SERVER_NAME=self.server_name,
        )

    @override_settings(URL_CONFIG="domain")
    def test_clarity_header_shows_the_repository_logo(self):
        self.repository.logo.name = "repos/5615/logo.png"
        self.repository.save()
        response = self.get_home()
        self.assertContains(response, self.repository.logo.url)
        self.assertNotContains(response, reverse("press_cover_download"))

    @override_settings(URL_CONFIG="domain")
    def test_clarity_header_without_a_repository_logo_skips_the_press_logo(self):
        response = self.get_home()
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, reverse("press_cover_download"))


class RepositoryListFilterTests(TestCase):
    """Covers the filter, sort and pagination paths of repository_list.

    Every one of these query strings raised UnboundLocalError before, because
    search_filters was only bound when a search term was present but was read
    unconditionally. They are driven through the real URL because that is the
    only place the bug shows up.
    """

    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.server_name = "filterrepo.test.com"
        cls.manager = helpers.create_user("filter_manager@janeway.systems")
        cls.repository, cls.subject = helpers.create_repository(
            cls.press,
            [cls.manager],
            [],
            domain=cls.server_name,
        )
        install.load_settings(cls.repository)
        cls.author = helpers.create_user(
            "filter_author@janeway.systems",
            first_name="Wilhelmina",
            last_name="Searchable",
        )
        cls.preprint = helpers.create_preprint(
            cls.repository,
            cls.author,
            cls.subject,
            title="Domesticating the ancient house",
            abstract="A study of the archaeology of a false analogy.",
        )
        cls.preprint.stage = rm.STAGE_PREPRINT_PUBLISHED
        cls.preprint.date_published = timezone.now()
        cls.preprint.save()

    def setUp(self):
        clear_script_prefix()

    @override_settings(URL_CONFIG="domain")
    def test_list_query_strings_do_not_error(self):
        for query in (
            "",
            "?page=1",
            "?subject={}".format(self.subject.pk),
            "?sort=title",
            "?sort=-date_published",
        ):
            with self.subTest(query=query):
                response = self.client.get(
                    "{}{}".format(reverse("repository_list"), query),
                    SERVER_NAME=self.server_name,
                )
                self.assertEqual(response.status_code, 200)

    @override_settings(URL_CONFIG="domain")
    def test_old_subject_url_redirects_and_resolves(self):
        response = self.client.get(
            reverse(
                "repository_list_subject",
                kwargs={"subject_id": self.subject.pk},
            ),
            SERVER_NAME=self.server_name,
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

    @override_settings(URL_CONFIG="domain")
    def test_search_finds_preprint_by_title_and_abstract(self):
        """A search box submits only search_term, with no field flags set.

        initial=True does not apply to bound forms, so without the form's
        clean() restoring the defaults every search matched nothing.
        """
        for term in ("Domesticating", "analogy"):
            with self.subTest(term=term):
                response = self.client.get(
                    "{}?search_term={}".format(reverse("repository_list"), term),
                    SERVER_NAME=self.server_name,
                )
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, self.preprint.title)

    @override_settings(URL_CONFIG="domain")
    def test_no_results_shows_an_empty_state_and_no_paginator(self):
        """Two testers reported a page 1 button sitting above zero results."""
        response = self.client.get(
            "{}?search_term=zzzznotathing".format(reverse("repository_list")),
            SERVER_NAME=self.server_name,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["preprints"].paginator.count, 0)
        self.assertContains(response, "No results found")
        self.assertNotContains(response, "page=1")

    @override_settings(URL_CONFIG="domain")
    def test_pagination_links_keep_the_active_filters(self):
        """Bare ?page=n links drop the reader's search, filter and sort."""
        response = self.client.get(
            "{}?search_term=Domesticating&sort=title".format(
                reverse("repository_list"),
            ),
            SERVER_NAME=self.server_name,
        )
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        for fragment in ("search_term=Domesticating", "sort=title"):
            self.assertIn(fragment, content)

    def test_search_matches_each_field_independently(self):
        """Joined fields are matched by subquery, not folded into the vector.

        Concatenating a search vector across a join made Postgres recompute the
        title and abstract vectors for every joined row.
        """
        cases = (
            ("Domesticating", {"title": True}),
            ("analogy", {"abstract": True}),
            ("Searchable", {"authors": True}),
        )
        base = {
            "title": False,
            "abstract": False,
            "authors": False,
            "keywords": False,
            "full_text": False,
            "ORCID": False,
        }
        for term, overrides in cases:
            with self.subTest(term=term, fields=sorted(overrides)):
                filters = dict(base)
                filters.update(overrides)
                results = rm.Preprint.objects.search(
                    term,
                    filters,
                    site=self.repository,
                )
                self.assertIn(self.preprint.pk, [item.pk for item in results])

    def test_search_does_not_match_a_field_that_is_switched_off(self):
        filters = {
            "title": True,
            "abstract": False,
            "authors": False,
            "keywords": False,
            "full_text": False,
            "ORCID": False,
        }
        results = rm.Preprint.objects.search(
            "Searchable",
            filters,
            site=self.repository,
        )
        self.assertEqual([item.pk for item in results], [])

    def test_search_filters_default_to_title_abstract_and_authors(self):
        form = forms.PreprintFilterForm(
            QueryDict("search_term=anything"),
            repository=self.repository,
        )
        self.assertTrue(form.is_valid())
        filters = form.search_filters()
        self.assertTrue(filters["title"])
        self.assertTrue(filters["abstract"])
        self.assertTrue(filters["authors"])
        self.assertFalse(filters["keywords"])

    def test_explicit_filters_are_not_overridden(self):
        form = forms.PreprintFilterForm(
            QueryDict("search_term=anything&keywords=on"),
            repository=self.repository,
        )
        self.assertTrue(form.is_valid())
        filters = form.search_filters()
        self.assertTrue(filters["keywords"])
        self.assertFalse(filters["title"])


class AffiliationDateTests(TestCase):
    """An affiliation must not end before it starts.

    No comparison against today, so a fixed term post with a future end date
    and one due to start next month both remain valid.
    """

    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.account = helpers.create_user("affiliation@janeway.systems")
        cls.organization = cm.Organization.objects.create()

    def build(self, start, end):
        return cm.ControlledAffiliation(
            account=self.account,
            organization=self.organization,
            start=start,
            end=end,
        )

    def test_end_before_start_is_rejected(self):
        affiliation = self.build(
            timezone.datetime(2045, 1, 1).date(),
            timezone.datetime(2026, 1, 1).date(),
        )
        with self.assertRaises(ValidationError):
            affiliation.full_clean(exclude=["organization"])

    def test_fixed_term_with_a_future_end_is_allowed(self):
        affiliation = self.build(
            timezone.datetime(2026, 1, 1).date(),
            timezone.datetime(2029, 12, 31).date(),
        )
        affiliation.full_clean(exclude=["organization"])

    def test_open_ended_affiliation_is_allowed(self):
        affiliation = self.build(timezone.datetime(2026, 1, 1).date(), None)
        affiliation.full_clean(exclude=["organization"])


class RepositoryDashboardQueryTests(TestCase):
    """The dashboard must not issue queries proportional to the row count.

    The live failure was a gunicorn worker timeout (Sentry OLH-JANEWAY-HCM),
    aborted mid-render resolving submission_type per row. The OAI import
    assigns a single owner to every record, so one account can own the whole
    corpus.
    """

    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.server_name = "dashrepo.test.com"
        cls.manager = helpers.create_user("dash_manager@janeway.systems")
        cls.repository, cls.subject = helpers.create_repository(
            cls.press,
            [cls.manager],
            [],
            domain=cls.server_name,
        )
        install.load_settings(cls.repository)
        cls.owner = helpers.create_user("dash_owner@janeway.systems")
        cls.owner.is_active = True
        cls.owner.save()
        cls.submission_type = rm.RepositorySubmissionType.objects.create(
            repository=cls.repository,
            name="Journal Article",
            name_plural="Journal Articles",
            slug="dash-journal-article",
        )
        for number in range(20):
            rm.Preprint.objects.create(
                repository=cls.repository,
                owner=cls.owner,
                submission_type=cls.submission_type,
                stage=rm.STAGE_PREPRINT_REVIEW,
                title="Preprint {}".format(number),
                abstract="",
                comments_editor="",
                date_submitted=timezone.now(),
            )

    def setUp(self):
        clear_script_prefix()

    @override_settings(URL_CONFIG="domain")
    def test_dashboard_query_count_is_independent_of_row_count(self):
        self.client.force_login(self.owner)

        def count_queries():
            with CaptureQueriesContext(connection) as queries:
                response = self.client.get(
                    reverse("repository_dashboard"),
                    SERVER_NAME=self.server_name,
                )
            self.assertEqual(response.status_code, 200)
            return len(queries)

        # Warm the session and settings caches so the baseline measures only
        # the per-row cost, not first-request overhead.
        count_queries()
        baseline = count_queries()
        for number in range(20, 60):
            rm.Preprint.objects.create(
                repository=self.repository,
                owner=self.owner,
                submission_type=self.submission_type,
                stage=rm.STAGE_PREPRINT_REVIEW,
                title="Extra preprint {}".format(number),
                abstract="",
                comments_editor="",
                date_submitted=timezone.now(),
            )
        self.assertEqual(baseline, count_queries())

    @override_settings(URL_CONFIG="domain")
    def test_dashboard_paginates(self):
        self.client.force_login(self.owner)
        response = self.client.get(
            reverse("repository_dashboard"),
            SERVER_NAME=self.server_name,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["preprints"]), 15)
