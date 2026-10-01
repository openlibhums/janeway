from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import override_settings
from django.urls import reverse

from repository import logic as repository_logic, models as rm
from repository.tests.test_frozen_authors import PreprintFrozenAuthorTestBase
from submission import models as sm


class VersionUpdateTestBase(PreprintFrozenAuthorTestBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.funding_field = rm.RepositoryField.objects.create(
            repository=cls.repository,
            name="Funding statement",
            input_type="textarea",
            required=False,
            order=1,
        )
        rm.RepositoryFieldAnswer.objects.create(
            field=cls.funding_field,
            preprint=cls.preprint,
            answer="Old grant",
        )
        cls.co_author, _ = sm.FrozenAuthor.snapshot_account_for_preprint(
            cls.co_author_account,
            cls.preprint,
        )
        cls.co_author.add_credit("writing-original-draft")

    def start(self, update_type="metadata_correction"):
        update, error = repository_logic.start_update(self.preprint, update_type)
        self.assertIsNone(error)
        return update

    def submit(self, update):
        self.assertIsNone(repository_logic.submit_update(update))
        update.refresh_from_db()
        return update

    def names(self, authors):
        return [author.full_name() for author in authors]

    def live_names(self):
        return self.names(self.preprint.frozen_authors())


class TestUpdateWorkflow(VersionUpdateTestBase):
    def test_draft_is_a_full_copy(self):
        update = self.start()
        self.assertEqual(self.names(update.authors), self.live_names())
        self.assertEqual(update.title, self.preprint.title)
        self.assertEqual(update.field_answers.get().answer, "Old grant")
        self.assertTrue(update.authors.get(author=self.co_author_account).credits)

    def test_one_open_update_at_a_time(self):
        update = self.start()
        self.assertEqual(self.start(), update)
        self.submit(update)
        again, error = repository_logic.start_update(self.preprint, "correction")
        self.assertIsNone(again)
        self.assertIsNotNone(error)

    def test_untouched_update_changes_nothing(self):
        # Data that copying or the editor could otherwise alter.
        self.co_author.affiliations.update(is_primary=False)
        self.preprint.abstract = "<p>One</p>\n<p>Two</p>"
        self.preprint.save()
        update = self.submit(self.start())
        self.assertEqual(update.changed_sections, [])
        self.assertEqual(update.sections_changed_since_started(), [])

    def test_approval_replaces_the_author_list(self):
        update = self.start()
        author_list = repository_logic.PreprintAuthorList(self.preprint, update)
        owner = update.authors.get(author=self.owner)
        owner.last_name = "Renamed"
        owner.save()
        author_list.reorder(update.authors.get(author=self.co_author_account), "top")
        sm.FrozenAuthor.objects.create(
            version_queue=update,
            first_name="New",
            last_name="Person",
            order=5,
        )
        old_version = self.preprint.current_version
        self.assertTrue(self.submit(update).approve())

        self.assertEqual(
            self.live_names(),
            ["Coral B Author", "Olive Renamed", "New Person"],
        )
        co_author = self.preprint.frozen_authors().get(author=self.co_author_account)
        self.assertEqual(co_author.institution, "Account Institute")
        self.assertEqual(
            [credit.role for credit in co_author.credits],
            ["writing-original-draft"],
        )
        old_version.refresh_from_db()
        self.assertEqual(
            self.names(old_version.authors),
            ["Olive Owner", "Coral B Author"],
        )

    def test_approval_keeps_moderator_changes_the_author_did_not_touch(self):
        update = self.start()
        # A moderator fixes the title and removes an author after the draft
        # started; the author only changes the custom fields.
        self.preprint.title = "Fixed title"
        self.preprint.save()
        self.co_author.delete()
        repository_logic.set_update_field_answers(
            update,
            {self.funding_field: "New grant"},
        )
        update = self.submit(update)
        self.assertEqual(update.changed_sections, ["field_answers"])
        self.assertEqual(
            update.sections_changed_since_started(),
            ["title", "authors"],
        )
        update.approve()

        self.preprint.refresh_from_db()
        self.assertEqual(self.preprint.title, "Fixed title")
        self.assertEqual(self.live_names(), ["Olive Owner"])
        self.assertEqual(
            self.preprint.repositoryfieldanswer_set.get().answer,
            "New grant",
        )

    def test_comparison_shows_what_approval_does_now(self):
        update = self.start()
        update.authors.get(author=self.owner).delete()
        update = self.submit(update)
        # The moderator renames the co-author while the update waits, so
        # approving would undo that.
        self.co_author.last_name = "Fixed"
        self.co_author.save()

        changes = update.author_changes()
        self.assertEqual(self.names(changes.removed), ["Olive Owner"])
        ((before, after, fields),) = changes.changed
        self.assertEqual(
            [(old, new) for _label, old, new in fields], [("Fixed", "Author")]
        )

    def test_clearing_values(self):
        self.preprint.doi = "https://doi.org/10.1234/wrong"
        self.preprint.save()
        update = self.start()
        update.published_doi = ""
        update.save()
        repository_logic.set_update_field_answers(update, {self.funding_field: ""})
        self.submit(update).approve()
        self.preprint.refresh_from_db()
        self.assertFalse(self.preprint.doi)
        self.assertFalse(self.preprint.repositoryfieldanswer_set.exists())

    def test_an_account_cannot_be_listed_twice(self):
        update = self.start()
        unlinked = sm.FrozenAuthor.objects.create(
            version_queue=update,
            first_name="Second",
            last_name="Copy",
            order=5,
        )
        unlinked.frozen_email = self.co_author_account.email
        unlinked.associate_with_account()
        self.assertIsNone(unlinked.author)

        unlinked.author = self.co_author_account
        with self.assertRaises(IntegrityError), transaction.atomic():
            unlinked.save()

    def test_metadata_correction_keeps_the_current_file(self):
        update = self.start("version")
        update.file = rm.PreprintFile.objects.create(
            preprint=self.preprint,
            original_filename="new.pdf",
        )
        update.save()
        update = self.start("metadata_correction")
        self.assertIsNone(update.file)
        self.assertFalse(
            rm.PreprintFile.objects.filter(original_filename="new.pdf").exists()
        )
        update.title = "A corrected title"
        update.save()
        self.submit(update).approve()
        self.assertEqual(self.preprint.current_version.file, self.version_file)

    def test_decline_applies_nothing(self):
        update = self.start()
        update.authors.get(author=self.owner).delete()
        versions = self.preprint.preprintversion_set.count()
        self.assertTrue(self.submit(update).decline())
        self.assertFalse(update.approve())
        self.assertEqual(self.live_names(), ["Olive Owner", "Coral B Author"])
        self.assertEqual(self.preprint.preprintversion_set.count(), versions)


class TestCompareAuthorLists(VersionUpdateTestBase):
    def test_matches_by_account_then_email_then_name(self):
        update = self.start()
        by_name = sm.FrozenAuthor.objects.create(
            preprint=self.preprint,
            first_name="Only",
            last_name="Name",
            order=3,
        )
        by_name.copy(preprint=None, version_queue=update)
        owner = update.authors.get(author=self.owner)
        owner.frozen_email = "olive.work@example.org"
        owner.save()

        changes = update.author_changes()
        self.assertEqual((changes.added, changes.removed), ([], []))
        self.assertEqual(
            [(old, new) for _label, old, new in changes.changed[0][2]],
            [("frozen_owner@janeway.systems", "olive.work@example.org")],
        )
        self.assertFalse(changes.reordered)


@override_settings(URL_CONFIG="domain")
class TestUpdateViews(VersionUpdateTestBase):
    def setUp(self):
        self.client.force_login(self.owner)

    def get(self, url):
        return self.client.get(url, SERVER_NAME=self.repository.domain)

    def post(self, url, data):
        return self.client.post(url, data, SERVER_NAME=self.repository.domain)

    def draft_url(self, update):
        return reverse("repository_update_draft", args=[self.preprint.pk, update.pk])

    def test_starting_an_update_is_a_post_by_the_owner(self):
        url = reverse("repository_submit_update", args=[self.preprint.pk, "version"])
        self.assertEqual(self.get(url).status_code, 405)
        self.client.force_login(self.co_author_account)
        self.assertEqual(self.post(url, {}).status_code, 404)
        self.client.force_login(self.owner)
        self.post(url, {})
        self.assertTrue(rm.VersionQueue.objects.filter(is_draft=True).exists())

    def test_others_cannot_open_the_draft(self):
        update = self.start()
        self.client.force_login(self.co_author_account)
        self.assertEqual(self.get(self.draft_url(update)).status_code, 403)

    def test_file_survives_author_changes_and_is_replaced(self):
        update = self.start("version")
        url = self.draft_url(update)
        for name in ("first.txt", "second.txt"):
            self.post(
                url,
                {
                    "upload_file": "",
                    "file": SimpleUploadedFile(name, b"Manuscript", "text/plain"),
                },
            )
        self.post(url, {"remove_author": update.authors.get(author=self.owner).pk})
        update.refresh_from_db()
        self.assertEqual(update.file.original_filename, "second.txt")
        self.assertFalse(
            rm.PreprintFile.objects.filter(original_filename="first.txt").exists()
        )

    def test_removed_author_can_be_restored(self):
        update = self.start()
        url = self.draft_url(update)
        self.post(url, {"remove_author": update.authors.get(author=self.owner).pk})
        self.assertContains(self.get(url), "data-removed-authors")
        self.post(url, {"restore_author": self.preprint.frozen_authors()[0].pk})
        self.assertFalse(update.author_changes().removed)

    def test_submit_from_the_draft_page(self):
        update = self.start()
        response = self.post(
            self.draft_url(update),
            {
                "submit_update": "",
                "title": self.preprint.title,
                "abstract": self.preprint.abstract,
                "published_doi": "",
                f"fields-field_{self.funding_field.pk}": "New grant",
            },
        )
        self.assertEqual(response.status_code, 302)
        update.refresh_from_db()
        self.assertFalse(update.is_draft)
        self.assertTrue(update.field_answers_changed)
        self.assertFalse(update.authors_changed)

    def test_queue_lists_submitted_updates_with_detail_buttons(self):
        draft_url = reverse("repository_version_detail", args=[self.start().pk])
        self.client.force_login(self.manager)
        response = self.get(reverse("version_queue"))
        self.assertNotContains(response, draft_url)

        update = self.submit(rm.VersionQueue.objects.get(is_draft=True))
        response = self.get(reverse("version_queue"))
        self.assertContains(
            response,
            f'<button type="button" class="button clear no-bottom-margin" '
            f'hx-get="{reverse("repository_version_detail", args=[update.pk])}"',
        )

    def test_moderator_detail_shows_changes(self):
        update = self.start()
        update.authors.get(author=self.owner).delete()
        update = self.submit(update)
        self.co_author.delete()
        url = reverse("repository_version_detail", args=[update.pk])

        self.assertEqual(self.get(url).status_code, 403)
        self.client.force_login(self.manager)
        response = self.get(url)
        self.assertContains(response, "data-changed-since-started")
        self.assertEqual(
            self.names(response.context["author_changes"].added), ["Coral B Author"]
        )
