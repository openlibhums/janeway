__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Andy Byers, Mauro Sanchez & Joseph Muller"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.test import Client, TestCase, override_settings
from django.shortcuts import reverse
from django.utils import timezone
from django.core import mail
from django.urls.base import clear_script_prefix

from utils.testing import helpers
from utils.install import update_settings
from core import models as cm
from repository import models as rm, install
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
        cls.staff_user = helpers.create_user("staff@janeway.systems")
        cls.staff_user.is_staff = True
        cls.staff_user.is_active = True
        cls.staff_user.save()
        cls.repository.managers.add(cls.staff_user)
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
    def test_press_manager_link_hidden_from_repository_manager(self):
        self.client.force_login(self.repo_manager)
        path = reverse("preprints_manager")
        response = self.client.get(path, SERVER_NAME=self.server_name)
        self.assertNotIn(b"Press Manager", response.content)

    @override_settings(URL_CONFIG="domain")
    def test_press_manager_link_shown_to_staff(self):
        self.client.force_login(self.staff_user)
        path = reverse("preprints_manager")
        response = self.client.get(path, SERVER_NAME=self.server_name)
        self.assertIn(b"Press Manager", response.content)


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
    def test_hierarchy_rou_view_returns_200(self):
        """Navigating to a specific ROU returns HTTP 200."""
        path = reverse("rou_hierarchy", kwargs={"rou_code": self.root.code})
        response = self.client.get(path, SERVER_NAME=self.server_name)
        self.assertEqual(response.status_code, 200)

    @override_settings(URL_CONFIG="domain")
    def test_hierarchy_rou_view_shows_preprints(self):
        """The selected-ROU page lists preprints belonging to that unit."""
        path = reverse("rou_hierarchy", kwargs={"rou_code": self.root.code})
        response = self.client.get(path, SERVER_NAME=self.server_name)
        self.assertContains(response, self.preprint.title)

    @override_settings(URL_CONFIG="domain")
    def test_hierarchy_unknown_rou_code_returns_404(self):
        """A request for a non-existent ROU code returns HTTP 404."""
        path = reverse("rou_hierarchy", kwargs={"rou_code": "does-not-exist"})
        response = self.client.get(path, SERVER_NAME=self.server_name)
        self.assertEqual(response.status_code, 404)
