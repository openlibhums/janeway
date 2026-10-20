from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from unittest import mock

from api import serializers
from events import logic as event_logic
from repository import logic as repository_logic, models as rm
from repository.tests.test_version_updates import VersionUpdateTestBase
from submission import models as sm
from utils.testing import helpers


class VersionQueueAPITestBase(VersionUpdateTestBase):
    def serializer(self, user=None, **payload):
        request = helpers.Request(
            repository=self.repository,
            user=user or self.owner,
        )
        data = {
            "preprint": self.preprint.pk,
            "update_type": "metadata_correction",
            "title": self.preprint.title,
        }
        data.update(payload)
        return serializers.VersionQueueCreateSerializer(
            data=data,
            context={"request": request},
        )

    def current_authors(self):
        return serializers.PreprintSerializer(self.preprint).data["authors"]

    def save(self, **payload):
        serializer = self.serializer(**payload)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        return serializer.save(), serializer

    def preprint_serializer(self, user, data):
        request = helpers.Request(repository=self.repository, user=user)
        return serializers.PreprintCreateSerializer(
            self.preprint,
            data=data,
            partial=True,
            context={"request": request},
        )


class TestVersionQueueCreateSerializer(VersionQueueAPITestBase):
    def test_unchanged_list_changes_nothing(self):
        update, _ = self.save(
            authors=self.current_authors(),
            additional_field_answers=[
                {"field": {"name": "Funding statement"}, "answer": "Old grant"}
            ],
        )
        self.assertFalse(update.is_draft)
        self.assertEqual(update.changed_sections, [])

    def test_full_list_is_applied_on_approval(self):
        authors = self.current_authors()[:1]
        authors[0]["last_name"] = "Renamed"
        authors.append(
            {
                "email": "new.author@example.org",
                "first_name": "New",
                "last_name": "Author",
                "institution": "New University",
                "orcid": "https://orcid.org/0000-0002-1825-0097",
            }
        )
        update, serializer = self.save(authors=authors)
        self.assertEqual(
            [f"{a['first_name']} {a['last_name']}" for a in serializer.data["authors"]],
            ["Olive Renamed", "New Author"],
        )

        update.approve()
        self.assertEqual(self.live_names(), ["Olive Renamed", "New Author"])
        new_author = self.preprint.frozen_authors().get(last_name="Author")
        self.assertEqual(new_author.frozen_orcid, "0000-0002-1825-0097")

    def test_authors_without_email_round_trip(self):
        sm.FrozenAuthor.objects.create(
            preprint=self.preprint,
            first_name="No",
            last_name="Email",
            order=5,
        )
        update, _ = self.save(authors=self.current_authors())
        self.assertFalse(update.authors_changed)

    def test_invalid_requests(self):
        other = helpers.create_preprint(
            self.repository,
            self.co_author_account,
            self.subject,
            title="Someone else's preprint",
        )
        other_file = rm.PreprintFile.objects.create(
            preprint=other,
            original_filename="other.pdf",
        )
        duplicates = self.current_authors()
        duplicates[1]["email"] = duplicates[0]["email"].upper()
        cases = {
            "authors": {"authors": duplicates},
            "additional_field_answers": {
                "additional_field_answers": [{"field": {"name": "Nope"}, "answer": "x"}]
            },
            "file": {"update_type": "version", "file": other_file.pk},
        }
        for key, payload in cases.items():
            with self.subTest(key):
                serializer = self.serializer(**payload)
                self.assertFalse(serializer.is_valid())
                self.assertIn(key, serializer.errors)

        for key, payload in (
            ("file", {"update_type": "version"}),
            ("file", {"file": self.version_file.pk}),
            ("error", {"user": self.manager}),
        ):
            with self.subTest(key):
                serializer = self.serializer(**payload)
                self.assertFalse(serializer.is_valid())
                self.assertIn(key, serializer.errors)

    def test_one_open_update_at_a_time(self):
        self.save()
        serializer = self.serializer()
        self.assertFalse(serializer.is_valid())
        self.assertIn("preprint", serializer.errors)

    @mock.patch("api.serializers.event_logic.Events.raise_event")
    def test_new_version_event_is_raised_after_commit(self, raise_event):
        serializer = self.serializer()
        self.assertTrue(serializer.is_valid(), serializer.errors)
        with self.captureOnCommitCallbacks(execute=True):
            update = serializer.save()
            raise_event.assert_not_called()

        raise_event.assert_called_once()
        args, kwargs = raise_event.call_args
        self.assertEqual(args[0], event_logic.Events.ON_PREPRINT_NEW_VERSION)
        self.assertEqual(kwargs["new_version"], update)
        self.assertEqual(kwargs["preprint"], self.preprint)


class TestOwnerCannotBypassModeration(VersionQueueAPITestBase):
    def test_owner_cannot_change_authors_answers_or_unsubmit(self):
        cases = {
            "authors": {"authors": self.current_authors()[:1]},
            "additional_field_answers": {
                "additional_field_answers": [
                    {"field": {"name": "Funding statement"}, "answer": "Changed"}
                ]
            },
            "date_submitted": {"date_submitted": None},
        }
        for key, data in cases.items():
            with self.subTest(key):
                serializer = self.preprint_serializer(self.owner, data)
                self.assertFalse(serializer.is_valid())
                self.assertIn(key, serializer.errors)

    def test_unchanged_authors_round_trip(self):
        self.co_author_account.orcid = "https://orcid.org/0000-0002-1825-0097"
        self.co_author_account.save()
        data = self.current_authors()
        self.assertEqual(data[1]["orcid"], "0000-0002-1825-0097")
        serializer = self.preprint_serializer(self.owner, {"authors": data})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_manager_can_change_authors(self):
        serializer = self.preprint_serializer(
            self.manager,
            {"authors": self.current_authors()[:1]},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)


@override_settings(URL_CONFIG="domain")
class TestVersionQueueEndpoint(VersionQueueAPITestBase):
    def test_lists_the_owners_submitted_updates(self):
        self.start()
        self.client.force_login(self.owner)
        url = reverse("repository_version_queue-list")
        response = self.client.get(url, SERVER_NAME=self.repository.domain)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"], [])

        self.save_draft_as_submitted()
        response = self.client.get(url, SERVER_NAME=self.repository.domain)
        (update,) = response.json()["results"]
        self.assertEqual(
            [author["last_name"] for author in update["authors"]],
            ["Owner", "Author"],
        )

    def save_draft_as_submitted(self):
        update = rm.VersionQueue.objects.get(is_draft=True)
        repository_logic.submit_update(update)


class TestPreprintFileUpload(VersionQueueAPITestBase):
    def test_only_the_owner_can_add_a_file(self):
        for user, valid in ((self.owner, True), (self.co_author_account, False)):
            request = helpers.Request(repository=self.repository, user=user)
            serializer = serializers.PreprintFileCreateSerializer(
                data={
                    "preprint": self.preprint.pk,
                    "original_filename": "upload.pdf",
                    "file": SimpleUploadedFile("upload.pdf", b"%PDF-1.4 test"),
                },
                context={"request": request},
            )
            self.assertEqual(serializer.is_valid(), valid)
