"""
Tests for preprint-related conflict resolutions from the iowa-and-isolinear integration.

NOTE: This file is intentionally in api/tests/ and named test_preprints.py so that
it runs AFTER test_preprint_oai.py alphabetically. The OAI tests hardcode object PKs
in expected XML output, so any test class that creates Preprint objects before them
will shift those PKs and cause failures.
"""

import mock
from uuid import uuid4

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from rest_framework.test import APIClient

from identifiers import forms as identifier_forms
from identifiers import models as identifier_models
from repository import models as repository_models
from utils.testing import helpers
from utils.setting_handler import save_setting


PREPRINT_FORMS_DOMAIN = "preprint-forms-test.domain.com"
PREPRINT_FORMS_DOMAIN_2 = "preprint-forms-test-2.domain.com"
PREPRINT_API_DOMAIN = "preprint-api-test.domain.com"


class TestIdentifierFormWithPreprint(TestCase):
    """
    Tests for IdentifierForm when used with preprints (commit 54 conflict resolution).

    The form gained a `preprint` kwarg alongside the existing `article` kwarg.
    DOI uniqueness is global; pubid uniqueness is scoped to the repository.
    """

    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.press.save()
        cls.author = helpers.create_user("preprint.identifier@test.com")

        cls.repo_one, cls.subject_one = helpers.create_repository(
            cls.press, [], [], domain=PREPRINT_FORMS_DOMAIN
        )
        cls.repo_two = repository_models.Repository.objects.create(
            press=cls.press,
            name="Second Test Repository",
            short_name="testrepo2",
            object_name="Preprint",
            object_name_plural="Preprints",
            publisher="Test Publisher",
            live=True,
            domain=PREPRINT_FORMS_DOMAIN_2,
        )
        cls.subject_two = repository_models.Subject.objects.create(
            repository=cls.repo_two,
            name="Repo Two Subject",
            slug="repo-two-subject",
            enabled=True,
        )

        cls.preprint_one = helpers.create_preprint(
            cls.repo_one, cls.author, cls.subject_one, title="Preprint One"
        )
        cls.preprint_one.make_new_version(cls.preprint_one.submission_file)

        cls.preprint_two = helpers.create_preprint(
            cls.repo_one, cls.author, cls.subject_one, title="Preprint Two"
        )
        cls.preprint_two.make_new_version(cls.preprint_two.submission_file)

        cls.preprint_other_repo = helpers.create_preprint(
            cls.repo_two, cls.author, cls.subject_two, title="Preprint Other Repo"
        )
        cls.preprint_other_repo.make_new_version(
            cls.preprint_other_repo.submission_file
        )

    def test_add_doi_to_preprint(self):
        """Can add a new DOI to a preprint."""
        form = identifier_forms.IdentifierForm(
            {"id_type": "doi", "identifier": "10.9999/preprint-new", "enabled": True},
            preprint=self.preprint_one,
        )
        self.assertTrue(form.is_valid())

    def test_add_pubid_to_preprint(self):
        """Can add a new pubid to a preprint."""
        form = identifier_forms.IdentifierForm(
            {"id_type": "pubid", "identifier": "preprint-new-pubid", "enabled": True},
            preprint=self.preprint_one,
        )
        self.assertTrue(form.is_valid())

    def test_duplicate_doi_same_repository(self):
        """Cannot add a DOI that already exists on another preprint in the same repository."""
        identifier_models.Identifier.objects.create(
            id_type="doi",
            identifier="10.9999/preprint-dup-doi",
            enabled=True,
            preprint_version=self.preprint_one.current_version,
        )
        form = identifier_forms.IdentifierForm(
            {
                "id_type": "doi",
                "identifier": "10.9999/preprint-dup-doi",
                "enabled": True,
            },
            preprint=self.preprint_two,
        )
        self.assertFalse(form.is_valid())

    def test_duplicate_doi_different_repositories(self):
        """DOIs must be globally unique: cannot reuse a DOI even across different repositories."""
        identifier_models.Identifier.objects.create(
            id_type="doi",
            identifier="10.9999/preprint-cross-repo-doi",
            enabled=True,
            preprint_version=self.preprint_one.current_version,
        )
        form = identifier_forms.IdentifierForm(
            {
                "id_type": "doi",
                "identifier": "10.9999/preprint-cross-repo-doi",
                "enabled": True,
            },
            preprint=self.preprint_other_repo,
        )
        self.assertFalse(form.is_valid())

    def test_duplicate_pubid_same_repository(self):
        """Cannot add a pubid that already exists in the same repository."""
        identifier_models.Identifier.objects.create(
            id_type="pubid",
            identifier="preprint-dup-pubid",
            enabled=True,
            preprint_version=self.preprint_one.current_version,
        )
        form = identifier_forms.IdentifierForm(
            {"id_type": "pubid", "identifier": "preprint-dup-pubid", "enabled": True},
            preprint=self.preprint_two,
        )
        self.assertFalse(form.is_valid())

    def test_duplicate_pubid_different_repositories_is_allowed(self):
        """The same pubid can exist in two different repositories."""
        identifier_models.Identifier.objects.create(
            id_type="pubid",
            identifier="preprint-shared-pubid",
            enabled=True,
            preprint_version=self.preprint_one.current_version,
        )
        form = identifier_forms.IdentifierForm(
            {
                "id_type": "pubid",
                "identifier": "preprint-shared-pubid",
                "enabled": True,
            },
            preprint=self.preprint_other_repo,
        )
        self.assertTrue(form.is_valid())


class TestCrossrefDepositParentObject(TestCase):
    """
    Tests for CrossrefDeposit.parent_object (commit 55 conflict resolution).

    The property replaced `journal` with `parent_object` so it can return either
    a Journal (for article DOIs) or a Repository (for preprint version DOIs).
    """

    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, _ = helpers.create_journals()
        save_setting("general", "journal_issn", cls.journal_one, "1234-5678")
        save_setting("general", "print_issn", cls.journal_one, "8765-4321")
        save_setting("Identifiers", "use_crossref", cls.journal_one, True)
        save_setting("Identifiers", "crossref_prefix", cls.journal_one, "10.0000")

        cls.author = helpers.create_user("deposit.parent@test.com")
        cls.repo, cls.subject = helpers.create_repository(
            cls.press, [], [], domain="deposit-parent-test.domain.com"
        )
        cls.article = helpers.create_article(cls.journal_one)
        cls.preprint = helpers.create_preprint(cls.repo, cls.author, cls.subject)
        cls.preprint.make_new_version(cls.preprint.submission_file)

    def _make_deposit_with_identifier(self, identifier):
        deposit = identifier_models.CrossrefDeposit.objects.create(
            document="<xml/>",
            file_name=uuid4(),
        )
        crossref_status, _ = identifier_models.CrossrefStatus.objects.get_or_create(
            identifier=identifier,
        )
        crossref_status.deposits.add(deposit)
        crossref_status.save()
        return deposit

    def test_parent_object_returns_journal_for_article_identifier(self):
        """parent_object returns the journal when the deposit covers article DOIs."""
        identifier = identifier_models.Identifier.objects.create(
            id_type="doi",
            identifier="10.0000/parent-obj-article-test",
            article=self.article,
        )
        deposit = self._make_deposit_with_identifier(identifier)
        self.assertEqual(deposit.parent_object, self.article.journal)

    def test_parent_object_returns_repository_for_preprint_identifier(self):
        """parent_object returns the repository when the deposit covers preprint DOIs."""
        identifier = identifier_models.Identifier.objects.create(
            id_type="doi",
            identifier="10.0000/parent-obj-preprint-test",
            preprint_version=self.preprint.current_version,
        )
        deposit = self._make_deposit_with_identifier(identifier)
        self.assertEqual(deposit.parent_object, self.repo)

    def test_parent_object_returns_none_with_no_linked_identifiers(self):
        """parent_object returns None when the deposit has no CrossrefStatus linked."""
        deposit = identifier_models.CrossrefDeposit.objects.create(
            document="<xml/>",
            file_name=uuid4(),
        )
        self.assertIsNone(deposit.parent_object)


class TestPreprintSubjectFilter(TestCase):
    """
    Tests for multi-subject filtering in PreprintViewSet (commit 59 conflict resolution).

    Iowa changed subject= from .get() (single value) to .getlist() (multiple values)
    so that ?subject=A&subject=B returns preprints in either subject.
    """

    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.repo, cls.subject_a = helpers.create_repository(
            cls.press, [], [], domain=PREPRINT_API_DOMAIN
        )
        cls.subject_b = repository_models.Subject.objects.create(
            repository=cls.repo,
            name="Subject B",
            slug="subject-b",
            enabled=True,
        )

        cls.author = helpers.create_user("preprint.api.filter@test.com")

        now = timezone.now()

        cls.preprint_a = helpers.create_preprint(
            cls.repo, cls.author, cls.subject_a, title="Preprint A"
        )
        cls.preprint_a.stage = repository_models.STAGE_PREPRINT_PUBLISHED
        cls.preprint_a.date_published = now
        cls.preprint_a.save()

        cls.preprint_b = helpers.create_preprint(
            cls.repo, cls.author, cls.subject_b, title="Preprint B"
        )
        cls.preprint_b.stage = repository_models.STAGE_PREPRINT_PUBLISHED
        cls.preprint_b.date_published = now
        cls.preprint_b.save()

        cls.api_client = APIClient()

    def _get_titles(self, response):
        results = response.data.get("results", response.data)
        return {r["title"] for r in results}

    @override_settings(URL_CONFIG="domain")
    def test_filter_by_single_subject_returns_matching_preprints(self):
        """?subject=X returns only preprints in that subject."""
        url = reverse("repository_published_preprint-list")
        response = self.api_client.get(
            url,
            {"subject": "Repo Subject"},
            SERVER_NAME=PREPRINT_API_DOMAIN,
        )
        self.assertEqual(response.status_code, 200)
        titles = self._get_titles(response)
        self.assertIn("Preprint A", titles)
        self.assertNotIn("Preprint B", titles)

    @override_settings(URL_CONFIG="domain")
    def test_filter_by_multiple_subjects_returns_all_matching(self):
        """?subject=A&subject=B returns preprints in either subject."""
        url = (
            reverse("repository_published_preprint-list")
            + "?subject=Repo+Subject&subject=Subject+B"
        )
        response = self.api_client.get(url, SERVER_NAME=PREPRINT_API_DOMAIN)
        self.assertEqual(response.status_code, 200)
        titles = self._get_titles(response)
        self.assertIn("Preprint A", titles)
        self.assertIn("Preprint B", titles)

    @override_settings(URL_CONFIG="domain")
    def test_no_subject_filter_returns_all_preprints(self):
        """Without a subject filter, all published preprints are returned."""
        url = reverse("repository_published_preprint-list")
        response = self.api_client.get(url, SERVER_NAME=PREPRINT_API_DOMAIN)
        self.assertEqual(response.status_code, 200)
        titles = self._get_titles(response)
        self.assertIn("Preprint A", titles)
        self.assertIn("Preprint B", titles)


ACCOUNT_ENDPOINTS_DOMAIN = "account-endpoints-test.domain.com"
CAN_EDIT_DOMAIN = "can-edit-preprint-test.domain.com"
PREPRINT_FILES_DOMAIN = "preprint-files-test.domain.com"


class TestAccountEndpointsGating(TestCase):
    """
    Tests for API_ENABLE_ACCOUNT_ENDPOINTS gating (iowa-and-isolinear).

    The URL registration happens at import time, so the routing test only
    works when the setting is False (the default). The queryset/search
    behaviour is tested directly via the view class.
    """

    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.press.save()
        cls.repo, cls.subject = helpers.create_repository(
            cls.press, [], [], domain=ACCOUNT_ENDPOINTS_DOMAIN
        )
        cls.searcher = helpers.create_user("acct.searcher@test.com")
        cls.target = helpers.create_user("exact.match@test.com")
        cls.api_client = APIClient()

    @override_settings(URL_CONFIG="domain")
    def test_account_search_not_routed_when_setting_disabled(self):
        """submission_account_search returns 404 when API_ENABLE_ACCOUNT_ENDPOINTS is False (default)."""
        response = self.api_client.get(
            "/api/submission_account_search/",
            SERVER_NAME=ACCOUNT_ENDPOINTS_DOMAIN,
        )
        self.assertEqual(response.status_code, 404)

    def test_account_search_queryset_returns_exact_email_match(self):
        """SubmissionAccountSearch queryset returns the account matching the exact email."""
        from api.views import SubmissionAccountSearch
        from rest_framework.test import APIRequestFactory

        factory = APIRequestFactory()
        request = factory.get(
            "/api/submission_account_search/",
            {"search": "exact.match@test.com"},
        )
        request.user = self.searcher
        request.repository = self.repo

        view = SubmissionAccountSearch()
        view.request = request
        qs = view.get_queryset()
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().email, "exact.match@test.com")

    def test_account_search_queryset_returns_nothing_for_partial_match(self):
        """Partial email strings return no results (exact-only semantics)."""
        from api.views import SubmissionAccountSearch
        from rest_framework.test import APIRequestFactory

        factory = APIRequestFactory()
        request = factory.get(
            "/api/submission_account_search/",
            {"search": "exact.match"},
        )
        request.user = self.searcher
        request.repository = self.repo

        view = SubmissionAccountSearch()
        view.request = request
        qs = view.get_queryset()
        self.assertEqual(qs.count(), 0)

    def test_account_search_queryset_returns_nothing_without_search_param(self):
        """An empty search parameter returns an empty queryset."""
        from api.views import SubmissionAccountSearch
        from rest_framework.test import APIRequestFactory

        factory = APIRequestFactory()
        request = factory.get("/api/submission_account_search/")
        request.user = self.searcher
        request.repository = self.repo

        view = SubmissionAccountSearch()
        view.request = request
        qs = view.get_queryset()
        self.assertEqual(qs.count(), 0)


class TestCanEditPreprintPermission(TestCase):
    """
    Tests for the CanEditPreprint DRF permission class (iowa-and-isolinear).

    GET requests are open to any authenticated user. PUT/PATCH/DELETE
    are limited to the preprint's owner and staff.
    """

    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.press.save()
        cls.repo, cls.subject = helpers.create_repository(
            cls.press, [], [], domain=CAN_EDIT_DOMAIN
        )
        cls.owner = helpers.create_user("preprint.owner@test.com")
        cls.other_user = helpers.create_user("preprint.other@test.com")
        cls.staff_user = helpers.create_user("preprint.staff@test.com")
        cls.staff_user.is_staff = True
        cls.staff_user.save()
        cls.preprint = helpers.create_preprint(
            cls.repo, cls.owner, cls.subject, title="Permission Test Preprint"
        )
        cls.api_client = APIClient()

    def _url(self, pk=None):
        if pk:
            return reverse("repository_user_preprints-detail", kwargs={"pk": pk})
        return reverse("repository_user_preprints-list")

    @override_settings(URL_CONFIG="domain")
    def test_owner_can_get_own_preprints(self):
        """Owner can GET their own preprint list."""
        self.api_client.force_authenticate(user=self.owner)
        response = self.api_client.get(self._url(), SERVER_NAME=CAN_EDIT_DOMAIN)
        self.assertEqual(response.status_code, 200)
        self.api_client.force_authenticate(user=None)

    @override_settings(URL_CONFIG="domain")
    def test_other_user_cannot_see_owners_preprints(self):
        """Another user's preprint list does not include someone else's preprints."""
        self.api_client.force_authenticate(user=self.other_user)
        response = self.api_client.get(self._url(), SERVER_NAME=CAN_EDIT_DOMAIN)
        self.assertEqual(response.status_code, 200)
        titles = [r["title"] for r in response.data.get("results", response.data)]
        self.assertNotIn("Permission Test Preprint", titles)
        self.api_client.force_authenticate(user=None)

    @override_settings(URL_CONFIG="domain")
    def test_non_owner_cannot_delete_preprint(self):
        """A non-owner receives 403 when attempting DELETE."""
        self.api_client.force_authenticate(user=self.other_user)
        response = self.api_client.delete(
            self._url(pk=self.preprint.pk), SERVER_NAME=CAN_EDIT_DOMAIN
        )
        self.assertEqual(response.status_code, 403)
        self.api_client.force_authenticate(user=None)

    def test_staff_can_edit_any_preprint(self):
        """CanEditPreprint grants staff permission for mutation methods."""
        from api.permissions import CanEditPreprint
        from rest_framework.test import APIRequestFactory

        factory = APIRequestFactory()
        request = factory.delete(f"/api/user_preprints/{self.preprint.pk}/")
        request.user = self.staff_user
        request.data = {}

        view = mock.Mock()
        view.kwargs = {"pk": self.preprint.pk}

        permission = CanEditPreprint()
        self.assertTrue(permission.has_permission(request, view))


class TestPreprintFilesScoping(TestCase):
    """
    Tests for PreprintFiles viewset queryset scoping (iowa-and-isolinear).

    PreprintFile objects are scoped to the request's repository AND the
    current user, so users cannot reach files belonging to other users'
    preprints.
    """

    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.press.save()
        cls.repo, cls.subject = helpers.create_repository(
            cls.press, [], [], domain=PREPRINT_FILES_DOMAIN
        )
        cls.owner = helpers.create_user("files.owner@test.com")
        cls.other_user = helpers.create_user("files.other@test.com")
        cls.preprint_owner = helpers.create_preprint(
            cls.repo, cls.owner, cls.subject, title="Owner Preprint"
        )
        cls.preprint_other = helpers.create_preprint(
            cls.repo, cls.other_user, cls.subject, title="Other Preprint"
        )
        cls.api_client = APIClient()

    def _url(self):
        return reverse("repository_preprint_files-list")

    @override_settings(URL_CONFIG="domain")
    def test_unauthenticated_request_is_rejected(self):
        """PreprintFiles endpoint requires authentication."""
        response = self.api_client.get(self._url(), SERVER_NAME=PREPRINT_FILES_DOMAIN)
        self.assertIn(response.status_code, [401, 403])

    @override_settings(URL_CONFIG="domain")
    def test_owner_sees_only_own_files(self):
        """The owner's file list only contains files from their own preprints."""
        self.api_client.force_authenticate(user=self.owner)
        response = self.api_client.get(self._url(), SERVER_NAME=PREPRINT_FILES_DOMAIN)
        self.assertEqual(response.status_code, 200)
        # submission_file created by create_preprint belongs to owner
        preprint_ids = {
            r["preprint"] for r in response.data.get("results", response.data)
        }
        self.assertNotIn(self.preprint_other.pk, preprint_ids)
        self.api_client.force_authenticate(user=None)
