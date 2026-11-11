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

    def draft_url(self, update):
        return reverse(
            "repository_update_draft",
            kwargs={"preprint_id": self.preprint.pk, "update_id": update.pk},
        )

    def start(self):
        update, error = self.logic.start_update(self.preprint, "metadata_correction")
        self.assertIsNone(error)
        return update

    def post_draft(self, update, data):
        self.client.force_login(self.owner)
        return self.client.post(
            self.draft_url(update), data, SERVER_NAME=self.repository.domain
        )

    def test_an_update_starts_with_a_copy_of_the_list(self):
        update = self.start()
        self.assertEqual([e.label for e in update.supplementary_files], ["Old data"])
        self.assertEqual(self.preprint.supplementaryfiles.count(), 1)

    def test_an_author_replaces_the_files_and_approval_applies_it(self):
        update = self.start()
        copy = update.supplementary_files.get()
        self.post_draft(update, {"remove_supplementary": copy.pk})
        self.post_draft(
            update,
            {
                "add_supplementary": "",
                "label": "Accepted manuscript",
                "document_version": "accepted",
                "access": "embargoed",
                "embargo_until": "2027-01-01",
                "upload": upload("aam.pdf", PDF, "application/pdf"),
            },
        )
        # Nothing changes on the record until it's approved.
        self.assertEqual(
            [e.label for e in self.preprint.supplementaryfiles], ["Old data"]
        )
        page = self.client.get(
            self.draft_url(update), SERVER_NAME=self.repository.domain
        )
        self.assertContains(page, "aam.pdf")

        self.assertIsNone(self.logic.submit_update(update))
        update.refresh_from_db()
        self.assertTrue(update.supplementary_files_changed)
        removed, added = update.supplementary_file_changes()
        self.assertEqual([e.label for e in removed], ["Old data"])
        self.assertEqual([e.label for e in added], ["Accepted manuscript"])

        first = self.preprint.current_version
        self.assertTrue(update.approve())
        entries = list(self.preprint.supplementaryfiles)
        self.assertEqual([e.label for e in entries], ["Accepted manuscript"])
        self.assertTrue(entries[0].file.is_locked())
        first.refresh_from_db()
        self.assertEqual([e.label for e in first.supplementary_files], ["Old data"])

    def test_an_update_that_leaves_the_files_doesnt_change_them(self):
        update = self.start()
        self.assertIsNone(self.logic.submit_update(update))
        update.refresh_from_db()
        self.assertFalse(update.supplementary_files_changed)
        self.assertTrue(update.approve())
        self.assertEqual(
            list(self.preprint.supplementaryfiles.values_list("pk", flat=True)),
            [self.link.pk],
        )

    def test_the_moderator_sees_the_change(self):
        update = self.start()
        self.post_draft(
            update,
            {"add_supplementary": "", "label": "Code", "url": "https://github.com/x/y"},
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
        self.post_draft(
            update,
            {
                "add_supplementary": "",
                "label": "Draft data",
                "upload": upload("draft.csv"),
            },
        )
        uploaded = update.supplementary_files.get(label="Draft data").file
        self.logic.discard_update(update)
        self.assertFalse(rm.PreprintFile.objects.filter(pk=uploaded.pk).exists())
        self.assertTrue(
            rm.PreprintSupplementaryFile.objects.filter(pk=self.link.pk).exists()
        )

    def test_a_draft_started_before_this_existed_leaves_the_files(self):
        update = self.start()
        started = dict(update.started_from)
        started.pop("supplementary_files")
        rm.VersionQueue.objects.filter(pk=update.pk).update(started_from=started)
        update.refresh_from_db()
        self.assertIsNone(self.logic.submit_update(update))
        update.refresh_from_db()
        self.assertFalse(update.supplementary_files_changed)
