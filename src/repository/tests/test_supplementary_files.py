from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils.http import urlencode
from freezegun import freeze_time

from api import serializers as api_serializers
from repository import forms, models as rm
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

    def test_an_authors_upload_to_a_published_record_waits_for_a_moderator(self):
        response = self.add(
            self.owner, {"label": "Publisher PDF"}, {"upload": upload()}
        )
        entry = self.preprint.supplementaryfiles.get()
        self.assertEqual(entry.file.access, rm.PreprintFile.ACCESS_RESTRICTED)
        self.assertEqual(self.get(entry.href).status_code, 403)
