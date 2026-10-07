from datetime import timedelta
from unittest import mock

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from rest_framework.test import APIClient

from repository import models as repository_models
from utils.testing import helpers

DOMAIN = "user-preprints-api.domain.com"


@override_settings(URL_CONFIG="domain")
class TestUserPreprintsAPI(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.repository, cls.subject = helpers.create_repository(
            cls.press, [], [], domain=DOMAIN
        )
        cls.other_repository = repository_models.Repository.objects.create(
            press=cls.press,
            name="Other",
            short_name="other",
            object_name="Preprint",
            object_name_plural="Preprints",
            publisher="Publisher",
            live=True,
            domain="other-user-preprints-api.domain.com",
        )
        cls.owner = helpers.create_user("owner@example.org")
        cls.someone_else = helpers.create_user("someone.else@example.org")
        cls.submitted = helpers.create_preprint(
            cls.repository, cls.owner, cls.subject, title="Submitted"
        )
        cls.draft = helpers.create_preprint(
            cls.repository, cls.owner, cls.subject, title="Draft"
        )
        cls.draft.stage = repository_models.STAGE_PREPRINT_UNSUBMITTED
        cls.draft.date_submitted = None
        cls.draft.save()

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.owner)

    def payload(self, **overrides):
        data = {
            "title": "A preprint",
            "abstract": "Abstract",
            "authors": [],
            "keywords": [],
            "subject": [],
            "additional_field_answers": [],
            "supplementary_files": [],
            "repository": self.repository.pk,
            "owner": self.owner.pk,
        }
        data.update(overrides)
        return data

    def send(self, method, data, pk=None):
        url = (
            reverse("repository_user_preprints-detail", kwargs={"pk": pk})
            if pk
            else reverse("repository_user_preprints-list")
        )
        return getattr(self.client, method)(
            url, data, format="json", SERVER_NAME=DOMAIN
        )

    def test_owners_cannot_publish_on_create(self):
        response = self.send(
            "post",
            self.payload(
                stage=repository_models.STAGE_PREPRINT_PUBLISHED,
                date_published="2020-01-01T00:00:00Z",
            ),
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(
            repository_models.Preprint.objects.filter(
                stage=repository_models.STAGE_PREPRINT_PUBLISHED,
            ).exists()
        )

    def test_created_preprints_are_submitted_for_moderation(self):
        response = self.send(
            "post",
            self.payload(
                date_published="2020-01-01T00:00:00Z",
                date_accepted="2020-01-01T00:00:00Z",
                preprint_doi="10.1234/mine",
                owner=self.someone_else.pk,
                repository=self.other_repository.pk,
            ),
        )
        self.assertEqual(response.status_code, 201)
        preprint = repository_models.Preprint.objects.get(pk=response.data["pk"])
        self.assertEqual(preprint.stage, repository_models.STAGE_PREPRINT_REVIEW)
        self.assertIsNotNone(preprint.date_submitted)
        self.assertIsNone(preprint.date_accepted)
        self.assertIsNone(preprint.date_published)
        self.assertIsNone(preprint.preprint_doi)
        self.assertEqual(preprint.owner, self.owner)
        self.assertEqual(preprint.repository, self.repository)

    def test_owners_cannot_publish_a_draft(self):
        response = self.send(
            "put",
            self.payload(
                stage=repository_models.STAGE_PREPRINT_PUBLISHED,
                date_published="2020-01-01T00:00:00Z",
            ),
            pk=self.draft.pk,
        )
        self.assertEqual(response.status_code, 400)
        self.draft.refresh_from_db()
        self.assertEqual(self.draft.stage, repository_models.STAGE_PREPRINT_UNSUBMITTED)

    @mock.patch("api.serializers.event_logic.Events.raise_event")
    def test_owners_can_submit_a_draft(self, raise_event):
        response = self.send(
            "put",
            self.payload(stage=repository_models.STAGE_PREPRINT_REVIEW),
            pk=self.draft.pk,
        )
        self.assertEqual(response.status_code, 200)
        self.draft.refresh_from_db()
        self.assertEqual(self.draft.stage, repository_models.STAGE_PREPRINT_REVIEW)
        self.assertIsNotNone(self.draft.date_submitted)
        raise_event.assert_called_once()

    def test_submitted_preprints_cannot_be_edited(self):
        response = self.send(
            "put",
            self.payload(
                title="Changed",
                stage=repository_models.STAGE_PREPRINT_REVIEW,
            ),
            pk=self.submitted.pk,
        )
        self.assertEqual(response.status_code, 403)
        self.submitted.refresh_from_db()
        self.assertEqual(self.submitted.title, "Submitted")

    def test_titles_are_sanitised(self):
        response = self.send(
            "post",
            self.payload(title="<i>Fine</i><script>alert(1)</script>"),
        )
        self.assertEqual(response.status_code, 201)
        preprint = repository_models.Preprint.objects.get(pk=response.data["pk"])
        self.assertNotIn("<script>", preprint.title)
        self.assertIn("<i>Fine</i>", preprint.title)


@override_settings(URL_CONFIG="domain")
class TestPreprintSearchAPI(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.manager = helpers.create_user("manager@example.org")
        cls.repository, cls.subject = helpers.create_repository(
            cls.press, [cls.manager], [], domain=DOMAIN
        )
        cls.other_repository = repository_models.Repository.objects.create(
            press=cls.press,
            name="Other",
            short_name="other",
            object_name="Preprint",
            object_name_plural="Preprints",
            publisher="Publisher",
            live=True,
            domain="other-search-api.domain.com",
        )
        other_subject = repository_models.Subject.objects.create(
            repository=cls.other_repository,
            name="Other subject",
            slug="other-subject",
            enabled=True,
        )
        author = helpers.create_user("author@example.org", last_name="Zebedee")
        cls.ours = helpers.create_preprint(
            cls.repository, author, cls.subject, title="Ours"
        )
        cls.theirs = helpers.create_preprint(
            cls.other_repository, author, other_subject, title="Theirs"
        )
        for preprint in (cls.ours, cls.theirs):
            preprint.stage = repository_models.STAGE_PREPRINT_PUBLISHED
            preprint.date_published = timezone.now() - timedelta(days=1)
            preprint.save()

    def test_author_search_stays_in_the_repository(self):
        client = APIClient()
        client.force_authenticate(user=self.manager)
        response = client.get(
            reverse("repository_preprints-list"),
            {"search": "Zebedee"},
            SERVER_NAME=DOMAIN,
        )
        self.assertEqual(response.status_code, 200)
        results = response.data.get("results", response.data)
        self.assertEqual([result["pk"] for result in results], [self.ours.pk])
