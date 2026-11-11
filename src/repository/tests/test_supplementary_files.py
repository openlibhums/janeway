from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils.http import urlencode
from freezegun import freeze_time

from api import serializers as api_serializers
from repository import forms, models as rm
from submission import models as sm
from repository.tests.test_file_access import MARKER, PDF, FileAccessTestBase

DATA = b"site,count\nBloomsbury,12\n"


def upload(name="data.csv", content=DATA, content_type="text/csv"):
    return SimpleUploadedFile(name, content, content_type=content_type)


@freeze_time("2026-11-11 12:00:00")
class SupplementaryFileTests(FileAccessTestBase):
    def setUp(self):
        super().setUp()
        self.preprint, self.main_file = self.published_preprint(
            PDF, "paper.pdf", "application/pdf"
        )

    def add(self, user, data, files=None):
        self.client.force_login(user)
        return self.client.post(
            reverse("repository_new_supplementary_files", args=[self.preprint.pk]),
            dict(data, form="", **(files or {})),
            SERVER_NAME=self.repository.domain,
        )

    def form(self, data, files=None, **kwargs):
        return forms.PreprintSupplementaryFileForm(
            data, files, preprint=self.preprint, **kwargs
        )

    # The form

    def test_preprint_servers_still_only_take_links(self):
        self.repository.repository_type = rm.Repository.TYPE_PREPRINT_SERVER
        self.repository.save()
        self.preprint.repository = self.repository
        form = self.form({"label": "Data"})
        self.assertNotIn("upload", form.fields)
        self.assertFalse(form.is_valid())
        self.assertIn("url", form.errors)
        form = self.form({"label": "Data", "url": "https://zenodo.org/records/1"})
        self.assertTrue(form.is_valid())

    def test_an_entry_is_a_link_or_an_upload(self):
        self.assertIn(
            "Give a link or upload a file.", str(self.form({"label": "Data"}).errors)
        )
        both = self.form(
            {"label": "Data", "url": "https://zenodo.org/records/1"},
            {"upload": upload()},
        )
        self.assertIn("not both", str(both.errors))

    def test_only_moderators_set_access(self):
        self.assertNotIn("access", self.form({}).fields)
        self.assertIn("access", self.form({}, can_set_access=True).fields)

    # Adding

    def test_a_manager_uploads_an_embargoed_accepted_manuscript(self):
        response = self.add(
            self.manager,
            {
                "label": "Accepted manuscript",
                "document_version": "accepted",
                "access": "embargoed",
                "embargo_until": "2027-01-01",
            },
            {"upload": upload("aam.pdf", PDF, "application/pdf")},
        )
        self.assertEqual(response.status_code, 302)
        entry = self.preprint.supplementaryfiles.get()
        self.assertTrue(entry.is_upload)
        self.assertEqual(entry.url, "")
        self.assertEqual(entry.file.original_filename, "aam.pdf")
        self.assertEqual(entry.file.document_version, "accepted")
        self.assertTrue(entry.is_locked)

    def test_an_authors_upload_before_publication_is_open(self):
        self.preprint.date_published = None
        self.preprint.save()
        self.add(
            self.owner,
            {"label": "Data", "access": "restricted"},
            {"upload": upload()},
        )
        entry = self.preprint.supplementaryfiles.get()
        self.assertEqual(entry.file.access, rm.PreprintFile.ACCESS_OPEN)

    def test_links_still_work(self):
        self.add(self.manager, {"label": "Code", "url": "https://github.com/x/y"})
        entry = self.preprint.supplementaryfiles.get()
        self.assertFalse(entry.is_upload)
        self.assertEqual(entry.href, "https://github.com/x/y")

    def test_a_supplementary_upload_in_the_submission_step_leaves_the_main_file(self):
        draft = rm.Preprint.objects.create(
            repository=self.repository, owner=self.owner, title="A draft"
        )
        self.client.force_login(self.owner)
        self.client.post(
            reverse("repository_files", args=[draft.pk]),
            {"form": "", "label": "Data", "upload": upload()},
            SERVER_NAME=self.repository.domain,
        )
        draft.refresh_from_db()
        self.assertIsNone(draft.submission_file)
        self.assertTrue(draft.supplementaryfiles.get().is_upload)

    # Public pages and downloads

    def add_upload(
        self, access=rm.PreprintFile.ACCESS_OPEN, content=DATA, name="data.csv"
    ):
        form = self.form(
            {
                "label": "Survey data",
                "document_version": "other",
                "access": access,
                "embargo_until": "2027-01-01",
            },
            {"upload": upload(name, content)},
            can_set_access=True,
        )
        self.assertTrue(form.is_valid(), form.errors)
        entry, _created = self.preprint.add_supplementary_file(form)
        return entry

    def test_an_open_upload_is_listed_and_downloads(self):
        entry = self.add_upload()
        for theme in ("OLH", "material", "clarity"):
            with self.subTest(theme=theme):
                self.repository.theme = theme
                self.repository.save()
                response = self.get(self.preprint.local_url)
                self.assertContains(response, "Survey data")
                self.assertContains(response, entry.href)
        download = self.get(entry.href)
        self.assertEqual(download.status_code, 200)
        self.assertEqual(b"".join(download.streaming_content), DATA)

    def test_a_locked_upload_is_listed_without_a_link_and_wont_download(self):
        entry = self.add_upload(
            rm.PreprintFile.ACCESS_EMBARGOED, content=MARKER.encode(), name="secret.txt"
        )
        for theme in ("OLH", "material", "clarity"):
            with self.subTest(theme=theme):
                self.repository.theme = theme
                self.repository.save()
                response = self.get(self.preprint.local_url)
                self.assertContains(response, "Survey data")
                self.assertContains(response, "Embargoed until 1 January 2027")
                self.assertNotContains(response, entry.href)
        self.assertEqual(self.get(entry.href).status_code, 403)
        self.assertEqual(self.get(entry.href, user=self.manager).status_code, 200)

    def test_files_from_other_preprints_are_not_served(self):
        other, other_file = self.published_preprint(
            PDF, "other.pdf", "application/pdf", title="Other"
        )
        url = reverse(
            "repository_file_download",
            kwargs={"preprint_id": self.preprint.pk, "file_id": other_file.pk},
        )
        self.assertEqual(self.get(url).status_code, 404)

    # Versions

    def test_a_superseded_version_keeps_its_supplementary_files(self):
        entry = self.add_upload()
        first = self.preprint.current_version
        new_file = rm.PreprintFile.objects.create(
            preprint=self.preprint,
            original_filename="v2.pdf",
            mime_type="application/pdf",
        )
        self.preprint.make_new_version(new_file)
        first.refresh_from_db()
        self.assertEqual([e.label for e in first.supplementary_files], ["Survey data"])
        self.assertEqual(first.supplementary_files[0].file, entry.file)

        # Deleting it from the current list keeps the file the snapshot uses.
        self.client.force_login(self.manager)
        self.client.post(
            reverse("repository_delete_supplementary_files", args=[self.preprint.pk]),
            {"delete": entry.pk},
            SERVER_NAME=self.repository.domain,
        )
        self.assertFalse(self.preprint.supplementaryfiles.exists())
        self.assertTrue(rm.PreprintFile.objects.filter(pk=entry.file_id).exists())
        self.assertEqual(self.get(first.supplementary_files[0].href).status_code, 200)

    def test_deleting_an_upload_nothing_else_uses_deletes_the_file(self):
        entry = self.add_upload()
        self.client.force_login(self.manager)
        self.client.post(
            reverse("repository_delete_supplementary_files", args=[self.preprint.pk]),
            {"delete": entry.pk},
            SERVER_NAME=self.repository.domain,
        )
        self.assertFalse(rm.PreprintFile.objects.filter(pk=entry.file_id).exists())

    # API and OAI

    def test_the_api_lists_uploads_and_hides_locked_ones(self):
        open_entry = self.add_upload()
        serialized = api_serializers.PreprintSupplementaryFileSerializer(
            open_entry
        ).data
        self.assertTrue(serialized["download_url"].endswith(open_entry.href))
        locked = self.add_upload(rm.PreprintFile.ACCESS_RESTRICTED, name="locked.csv")
        self.assertIsNone(
            api_serializers.PreprintSupplementaryFileSerializer(locked).data[
                "download_url"
            ]
        )

    def test_oai_records_leave_out_locked_files(self):
        self.lock(self.main_file)
        locked = self.add_upload(rm.PreprintFile.ACCESS_RESTRICTED, name="locked.csv")
        for prefix in ("oai_dc", "jats"):
            with self.subTest(prefix=prefix):
                response = self.client.get(
                    "{}?{}".format(
                        reverse("OAI_list_records"),
                        urlencode(
                            {
                                "verb": "GetRecord",
                                "metadataPrefix": prefix,
                                "identifier": "oai:{}:id:{}".format(
                                    self.repository.short_name, self.preprint.pk
                                ),
                            }
                        ),
                    ),
                    SERVER_NAME=self.repository.domain,
                )
                self.assertEqual(response.status_code, 200)
                content = response.content.decode()
                self.assertIn(self.preprint.title, content)
                self.assertNotIn(
                    self.download_url(self.preprint, self.main_file), content
                )
                self.assertNotIn(locked.href, content)

    def test_authors_change_a_published_records_files_through_an_update(self):
        response = self.add(
            self.owner, {"label": "Publisher PDF"}, {"upload": upload()}
        )
        self.assertRedirects(
            response,
            reverse("repository_author_article", args=[self.preprint.pk]),
            fetch_redirect_response=False,
        )
        self.assertFalse(self.preprint.supplementaryfiles.exists())
        # Moderators still edit them directly.
        self.add(self.manager, {"label": "Data", "url": "https://zenodo.org/records/1"})
        self.assertTrue(self.preprint.supplementaryfiles.exists())

    def test_called_additional_files_on_institutional_repositories(self):
        self.add_upload()
        self.assertContains(self.get(self.preprint.local_url), "Additional files")
        self.repository.repository_type = rm.Repository.TYPE_PREPRINT_SERVER
        self.repository.save()
        response = self.get(self.preprint.local_url)
        self.assertContains(response, "Supplementary files")
        self.assertNotContains(response, "Additional files")


@freeze_time("2026-11-11 12:00:00")
class UpdateSupplementaryFileTests(FileAccessTestBase):
    """Additional files go through updates, as authors do."""

    def setUp(self):
        super().setUp()
        from repository import logic as repository_logic

        self.logic = repository_logic
        self.preprint, self.main_file = self.published_preprint(
            PDF, "paper.pdf", "application/pdf"
        )
        sm.FrozenAuthor.objects.create(
            preprint=self.preprint,
            first_name="Ada",
            last_name="Author",
            order=0,
            frozen_email="ada@author.example",
        )
        self.link = rm.PreprintSupplementaryFile.objects.create(
            preprint=self.preprint, url="https://zenodo.org/records/1", label="Old data"
        )
        self.shared = rm.PreprintFile.objects.create(
            preprint=self.preprint, original_filename="counts.csv", mime_type="text/csv"
        )
        self.upload_entry = rm.PreprintSupplementaryFile.objects.create(
            preprint=self.preprint, file=self.shared, label="Counts", order=1
        )

    def draft_url(self, update):
        return reverse(
            "repository_update_draft",
            kwargs={"preprint_id": self.preprint.pk, "update_id": update.pk},
        )

    def files_url(self, update):
        return reverse(
            "repository_update_additional_files",
            kwargs={"preprint_id": self.preprint.pk, "update_id": update.pk},
        )

    def start(self):
        update, error = self.logic.start_update(self.preprint, "metadata_correction")
        self.assertIsNone(error)
        return update

    def act(self, update, data, htmx=True):
        self.client.force_login(self.owner)
        headers = {"HTTP_HX_REQUEST": "true"} if htmx else {}
        return self.client.post(
            self.files_url(update), data, SERVER_NAME=self.repository.domain, **headers
        )

    def draft_entry(self, update, label):
        return update.supplementary_files.get(label=label)

    def test_an_update_starts_with_a_copy_of_the_list(self):
        update = self.start()
        self.assertEqual(
            [e.label for e in update.supplementary_files], ["Old data", "Counts"]
        )

    def test_changes_happen_in_place_and_are_marked(self):
        update = self.start()
        response = self.act(
            update,
            {"action": "link", "link-url": "https://github.com/x/y", "link-label": ""},
        )
        # Only the block comes back (htmx swaps it), so the draft's unsaved
        # details are untouched.
        self.assertNotContains(response, "<html")
        self.assertContains(response, 'id="additional-files"')
        self.assertContains(
            response, "https://github.com/x/y"
        )  # the label defaults to it
        self.assertContains(response, "New")

        old = self.draft_entry(update, "Old data")
        response = self.act(update, {"action": "remove", "entry": old.pk})
        self.assertContains(response, "<del>Old data</del>")
        self.assertContains(response, "Undo")

        response = self.act(update, {"action": "restore", "entry": self.link.pk})
        self.assertNotContains(response, "<del>Old data</del>")
        self.assertEqual(update.supplementary_files.filter(label="Old data").count(), 1)

    def test_without_javascript_it_goes_back_to_the_draft(self):
        update = self.start()
        response = self.act(
            update,
            {
                "action": "link",
                "link-url": "https://github.com/x/y",
                "link-label": "Code",
            },
            htmx=False,
        )
        self.assertRedirects(
            response,
            self.draft_url(update) + "#additional-files",
            fetch_redirect_response=False,
        )

    def test_uploads_get_their_file_name_as_label_and_their_access(self):
        update = self.start()
        self.act(
            update,
            {
                "action": "upload",
                "upload-upload": upload("questionnaire.pdf", PDF, "application/pdf"),
                "upload-label": "",
                "upload-document_version": "accepted",
                "upload-access": "embargoed",
                "upload-embargo_until": "2027-03-01",
            },
        )
        entry = self.draft_entry(update, "questionnaire.pdf")
        self.assertEqual(entry.file.access, "embargoed")
        self.assertEqual(entry.file.document_version, "accepted")

    def test_an_embargo_needs_an_end_date(self):
        update = self.start()
        response = self.act(
            update,
            {
                "action": "upload",
                "upload-upload": upload(),
                "upload-access": "embargoed",
                "upload-embargo_until": "",
            },
        )
        self.assertContains(response, "Give the date the embargo ends.")
        self.assertEqual(update.supplementary_files.count(), 2)

    def test_editing_a_shared_files_access_waits_for_approval(self):
        update = self.start()
        entry = self.draft_entry(update, "Counts")
        prefix = "edit-{}".format(entry.pk)
        response = self.act(
            update,
            {
                "action": "edit",
                "entry": entry.pk,
                prefix + "-label": "Trial counts",
                prefix + "-document_version": "other",
                prefix + "-access": "embargoed",
                prefix + "-embargo_until": "2027-01-01",
            },
        )
        self.assertContains(response, "Changed")
        self.shared.refresh_from_db()
        self.assertEqual(
            self.shared.access, "open"
        )  # the live record's file is untouched
        entry.refresh_from_db()
        self.assertEqual(entry.proposed_access, "embargoed")

        self.assertIsNone(self.logic.submit_update(update))
        update.refresh_from_db()
        self.assertTrue(update.supplementary_files_changed)
        self.assertTrue(update.approve())
        self.shared.refresh_from_db()
        self.assertEqual(self.shared.access, "embargoed")
        self.assertEqual(self.shared.embargo_until.isoformat(), "2027-01-01")
        self.assertEqual(
            list(self.preprint.supplementaryfiles.values_list("label", flat=True)),
            ["Old data", "Trial counts"],
        )

    def test_replacing_a_file(self):
        update = self.start()
        entry = self.draft_entry(update, "Counts")
        prefix = "edit-{}".format(entry.pk)
        self.act(
            update,
            {
                "action": "edit",
                "entry": entry.pk,
                prefix + "-label": "Counts",
                prefix + "-replace": upload("counts-v2.csv"),
                prefix + "-access": "open",
            },
        )
        entry.refresh_from_db()
        self.assertEqual(entry.file.original_filename, "counts-v2.csv")
        self.assertTrue(rm.PreprintFile.objects.filter(pk=self.shared.pk).exists())

    def test_approval_replaces_the_list_and_the_old_version_keeps_it(self):
        update = self.start()
        self.act(
            update,
            {"action": "remove", "entry": self.draft_entry(update, "Old data").pk},
        )
        self.assertIsNone(self.logic.submit_update(update))
        update.refresh_from_db()
        first = self.preprint.current_version
        self.assertTrue(update.approve())
        self.assertEqual(
            list(self.preprint.supplementaryfiles.values_list("label", flat=True)),
            ["Counts"],
        )
        first.refresh_from_db()
        self.assertEqual(
            [e.label for e in first.supplementary_files], ["Old data", "Counts"]
        )

    def test_an_update_that_leaves_the_files_doesnt_change_them(self):
        update = self.start()
        self.assertIsNone(self.logic.submit_update(update))
        update.refresh_from_db()
        self.assertFalse(update.supplementary_files_changed)

    def test_the_moderator_sees_the_change(self):
        update = self.start()
        self.act(
            update,
            {
                "action": "link",
                "link-url": "https://github.com/x/y",
                "link-label": "Code",
            },
        )
        self.logic.submit_update(update)
        self.client.force_login(self.manager)
        response = self.client.get(
            reverse("repository_version_detail", kwargs={"update_id": update.pk}),
            SERVER_NAME=self.repository.domain,
        )
        self.assertContains(response, "data-supplementary-changes")
        self.assertContains(response, "https://github.com/x/y")

    def test_discarding_deletes_files_only_the_draft_used(self):
        update = self.start()
        self.act(
            update,
            {
                "action": "upload",
                "upload-upload": upload("draft.csv"),
                "upload-access": "open",
            },
        )
        uploaded = self.draft_entry(update, "draft.csv").file
        self.logic.discard_update(update)
        self.assertFalse(rm.PreprintFile.objects.filter(pk=uploaded.pk).exists())
        self.assertTrue(rm.PreprintFile.objects.filter(pk=self.shared.pk).exists())

    def test_a_draft_started_before_this_existed_leaves_the_files(self):
        update = self.start()
        started = dict(update.started_from)
        started.pop("supplementary_files")
        rm.VersionQueue.objects.filter(pk=update.pk).update(started_from=started)
        update.refresh_from_db()
        self.assertIsNone(self.logic.submit_update(update))
        update.refresh_from_db()
        self.assertFalse(update.supplementary_files_changed)

    def test_the_edit_button_starts_an_update_at_the_files(self):
        self.client.force_login(self.owner)
        page = self.client.get(
            reverse("repository_author_article", args=[self.preprint.pk]),
            SERVER_NAME=self.repository.domain,
        )
        self.assertContains(page, "data-edit-additional-files")
        response = self.client.post(
            reverse(
                "repository_submit_update",
                args=[self.preprint.pk, "metadata_correction"],
            ),
            {"section": "additional_files"},
            SERVER_NAME=self.repository.domain,
        )
        update = rm.VersionQueue.objects.get(preprint=self.preprint)
        self.assertRedirects(
            response,
            self.draft_url(update) + "#additional-files",
            fetch_redirect_response=False,
        )

    def test_the_edit_button_keeps_an_open_drafts_type(self):
        update, _error = self.logic.start_update(self.preprint, "version")
        self.client.force_login(self.owner)
        self.client.post(
            reverse(
                "repository_submit_update",
                args=[self.preprint.pk, "metadata_correction"],
            ),
            {"section": "additional_files"},
            SERVER_NAME=self.repository.domain,
        )
        update.refresh_from_db()
        self.assertEqual(update.update_type, "version")

    def test_a_new_file_in_an_update_starts_with_the_old_files_lock(self):
        self.lock(self.main_file)
        update, _error = self.logic.start_update(self.preprint, "correction")
        self.client.force_login(self.owner)
        self.client.post(
            self.draft_url(update),
            {"upload_file": "", "file": upload("v2.pdf", PDF, "application/pdf")},
            SERVER_NAME=self.repository.domain,
        )
        update.refresh_from_db()
        self.assertTrue(update.file.is_locked())
        page = self.client.get(
            self.draft_url(update), SERVER_NAME=self.repository.domain
        )
        self.assertContains(page, "data-file-access")
        # The author opens it; approval keeps their choice.
        self.client.post(
            self.draft_url(update),
            {"save_file_access": "", "file_access-access": "open"},
            SERVER_NAME=self.repository.domain,
        )
        update.file.refresh_from_db()
        self.assertFalse(update.file.is_locked())
        self.assertIsNone(self.logic.submit_update(update))
        update.refresh_from_db()
        self.assertTrue(update.approve())
        self.assertFalse(self.preprint.current_version.file.is_locked())
