import datetime
import shutil
import tempfile
from unittest import mock

from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.urls.base import clear_script_prefix
from django.utils import timezone
from freezegun import freeze_time

from repository import models as rm
from utils import models as utils_models
from utils.testing import helpers

MARKER = "Zanzibarquetzal"
HTML = "<html><body><p>The secret result: {}.</p></body></html>".format(MARKER)
PDF = b"%PDF-1.4\n% " + MARKER.encode() + b"\n%%EOF"
SEARCH_FILTERS = {
    "title": False,
    "abstract": False,
    "authors": False,
    "keywords": False,
    "full_text": True,
    "ORCID": False,
}


@override_settings(URL_CONFIG="domain")
class FileAccessTestBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.manager = helpers.create_user("access_manager@janeway.systems")
        cls.owner = helpers.create_user("access_owner@janeway.systems")
        cls.reader = helpers.create_user("access_reader@janeway.systems")
        cls.staff = helpers.create_user("access_staff@janeway.systems")
        cls.staff.is_staff = True
        for account in (cls.manager, cls.owner, cls.reader, cls.staff):
            account.is_active = True
            account.save()
        cls.repository, cls.subject = helpers.create_repository(
            cls.press, [cls.manager], [], domain="ir.test.com"
        )
        cls.repository.repository_type = rm.Repository.TYPE_INSTITUTIONAL
        cls.repository.save()

    def setUp(self):
        clear_script_prefix()
        # Files go to a temporary folder, never the install's files/.
        self.storage = rm.preprint_file_store
        self.storage_location = self.storage._location
        self.files_root = tempfile.mkdtemp(prefix="file-access-test-")
        self.storage._location = self.files_root
        for attr in ("base_location", "location"):
            self.storage.__dict__.pop(attr, None)

    def tearDown(self):
        self.storage._location = self.storage_location
        for attr in ("base_location", "location"):
            self.storage.__dict__.pop(attr, None)
        shutil.rmtree(self.files_root, ignore_errors=True)
        super().tearDown()

    def published_preprint(
        self, content, filename, mime_type, title="An embargoed study"
    ):
        preprint = helpers.create_preprint(
            self.repository, self.owner, self.subject, title=title
        )
        preprint.stage = rm.STAGE_PREPRINT_PUBLISHED
        preprint.date_published = timezone.now() - datetime.timedelta(days=1)
        preprint.save()
        preprint_file = rm.PreprintFile(
            preprint=preprint, original_filename=filename, mime_type=mime_type
        )
        preprint_file.file.save(filename, ContentFile(content), save=False)
        if mime_type == "application/pdf":
            # The test PDF is too small for pdfminer; HTML files are indexed.
            with mock.patch.object(rm.PreprintFile, "index_full_text"):
                preprint_file.save()
        else:
            preprint_file.save()
        preprint.make_new_version(preprint_file)
        return preprint, preprint_file

    def lock(
        self, preprint_file, access=rm.PreprintFile.ACCESS_EMBARGOED, until="2027-01-01"
    ):
        preprint_file.access = access
        preprint_file.embargo_until = (
            datetime.date.fromisoformat(until) if until else None
        )
        preprint_file.save(update_fields=["access", "embargo_until"])

    def get(self, url, user=None, **params):
        if user:
            self.client.force_login(user)
        else:
            self.client.logout()
        return self.client.get(url, params, SERVER_NAME=self.repository.domain)

    def download_url(self, preprint, preprint_file):
        return reverse(
            "repository_file_download",
            kwargs={"preprint_id": preprint.pk, "file_id": preprint_file.pk},
        )


class IsLockedTests(TestCase):
    def file(self, access, until=None):
        return rm.PreprintFile(access=access, embargo_until=until)

    def test_open_files_are_never_locked(self):
        self.assertFalse(self.file(rm.PreprintFile.ACCESS_OPEN).is_locked())

    def test_an_embargo_locks_until_its_end_date(self):
        embargoed = self.file(
            rm.PreprintFile.ACCESS_EMBARGOED, datetime.date(2027, 1, 1)
        )
        self.assertTrue(embargoed.is_locked(on=datetime.date(2026, 12, 31)))
        self.assertFalse(embargoed.is_locked(on=datetime.date(2027, 1, 1)))

    def test_an_embargo_without_an_end_stays_locked(self):
        self.assertTrue(self.file(rm.PreprintFile.ACCESS_EMBARGOED).is_locked())

    def test_restricted_files_are_always_locked(self):
        restricted = self.file(
            rm.PreprintFile.ACCESS_RESTRICTED, datetime.date(2000, 1, 1)
        )
        self.assertTrue(restricted.is_locked())

    def test_labels(self):
        with freeze_time("2026-11-11"):
            embargoed = self.file(
                rm.PreprintFile.ACCESS_EMBARGOED, datetime.date(2027, 1, 1)
            )
            self.assertEqual(
                str(embargoed.access_label), "Embargoed until 1 January 2027"
            )
            self.assertEqual(
                str(self.file(rm.PreprintFile.ACCESS_RESTRICTED).access_label),
                "Restricted to repository staff",
            )
            self.assertEqual(self.file(rm.PreprintFile.ACCESS_OPEN).access_label, "")


@freeze_time("2026-11-11 12:00:00")
class LeakTests(FileAccessTestBase):
    """A locked file's bytes and text must not reach the public by any route."""

    def assert_page_hides_the_file(self, preprint, preprint_file):
        for theme in ("OLH", "material", "clarity"):
            with self.subTest(theme=theme):
                self.repository.theme = theme
                self.repository.save()
                response = self.get(preprint.local_url)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "Embargoed until 1 January 2027")
                self.assertNotContains(response, MARKER)
                self.assertNotContains(
                    response, self.download_url(preprint, preprint_file)
                )
                self.assertNotContains(response, "citation_pdf_url")
                self.assertNotContains(response, "<iframe")

    def test_a_locked_pdf_is_not_on_the_page_or_in_the_meta_tags(self):
        preprint, preprint_file = self.published_preprint(
            PDF, "paper.pdf", "application/pdf"
        )
        self.repository.theme = "material"  # OLH has no citation meta tags
        self.repository.save()
        response = self.get(preprint.local_url)
        self.assertContains(response, "citation_pdf_url")
        self.assertContains(response, self.download_url(preprint, preprint_file))

        self.lock(preprint_file)
        self.assert_page_hides_the_file(preprint, preprint_file)

    def test_a_locked_html_file_is_not_rendered_on_the_page(self):
        preprint, preprint_file = self.published_preprint(
            HTML.encode(), "paper.html", "text/html"
        )
        self.assertContains(self.get(preprint.local_url), MARKER)

        self.lock(preprint_file)
        self.assert_page_hides_the_file(preprint, preprint_file)
        self.assertEqual(preprint.current_version.render(), "")
        self.assertEqual(preprint.current_version.html(), "")

    def test_the_public_cannot_download_a_locked_file(self):
        preprint, preprint_file = self.published_preprint(
            PDF, "paper.pdf", "application/pdf"
        )
        self.lock(preprint_file)
        url = self.download_url(preprint, preprint_file)
        for user in (None, self.reader):
            for params in ({}, {"embed": "1"}):
                with self.subTest(user=user, params=params):
                    response = self.get(url, user=user, **params)
                    self.assertEqual(response.status_code, 403)
                    self.assertNotIn(MARKER.encode(), b"".join(response))

    def test_restricted_files_are_locked_for_good(self):
        preprint, preprint_file = self.published_preprint(
            PDF, "paper.pdf", "application/pdf"
        )
        self.lock(preprint_file, rm.PreprintFile.ACCESS_RESTRICTED, until=None)
        self.assertEqual(
            self.get(self.download_url(preprint, preprint_file)).status_code, 403
        )
        with freeze_time("2099-01-01"):
            self.assertEqual(
                self.get(self.download_url(preprint, preprint_file)).status_code, 403
            )
            self.assertContains(
                self.get(preprint.local_url), "Restricted to repository staff"
            )

    def test_owner_managers_and_staff_can_download_a_locked_file_uncounted(self):
        preprint, preprint_file = self.published_preprint(
            PDF, "paper.pdf", "application/pdf"
        )
        self.lock(preprint_file)
        for user in (self.owner, self.manager, self.staff):
            with self.subTest(user=user):
                response = self.get(
                    self.download_url(preprint, preprint_file), user=user
                )
                self.assertEqual(response.status_code, 200)
                self.assertIn(MARKER.encode(), b"".join(response.streaming_content))
        self.assertFalse(rm.PreprintAccess.objects.filter(preprint=preprint).exists())

    def test_a_locked_files_text_is_not_searched(self):
        preprint, preprint_file = self.published_preprint(
            HTML.encode(), "paper.html", "text/html"
        )
        preprint_file.refresh_from_db()
        self.assertIsNotNone(
            preprint_file.text, "the HTML file should have been indexed"
        )

        def found():
            results = rm.Preprint.objects.search(
                MARKER, SEARCH_FILTERS, site=self.repository
            )
            return preprint.pk in [result.pk for result in results]

        self.assertTrue(found())
        self.lock(preprint_file)
        self.assertFalse(found())

    def test_the_file_opens_on_its_embargo_end_date(self):
        preprint, preprint_file = self.published_preprint(
            PDF, "paper.pdf", "application/pdf"
        )
        self.lock(preprint_file)
        with freeze_time("2027-01-01 09:00:00"):
            response = self.get(preprint.local_url)
            self.assertContains(response, self.download_url(preprint, preprint_file))
            self.assertNotContains(response, "Embargoed until")
            download = self.get(self.download_url(preprint, preprint_file))
            self.assertEqual(download.status_code, 200)


@freeze_time("2026-11-11 12:00:00")
class FileAccessFormTests(FileAccessTestBase):
    def setUp(self):
        super().setUp()
        self.preprint, self.preprint_file = self.published_preprint(
            PDF, "paper.pdf", "application/pdf"
        )
        self.url = reverse(
            "repository_file_access",
            kwargs={"preprint_id": self.preprint.pk, "file_id": self.preprint_file.pk},
        )

    def post(self, data, user=None):
        self.client.force_login(user or self.manager)
        return self.client.post(self.url, data, SERVER_NAME=self.repository.domain)

    def test_a_manager_embargoes_a_file(self):
        response = self.post(
            {
                "access": "embargoed",
                "embargo_until": "2027-01-01",
                "document_version": "accepted",
            }
        )
        self.assertEqual(response.status_code, 302)
        self.preprint_file.refresh_from_db()
        self.assertTrue(self.preprint_file.is_locked())
        self.assertEqual(self.preprint_file.embargo_until, datetime.date(2027, 1, 1))
        self.assertEqual(self.preprint_file.document_version, "accepted")
        self.assertTrue(
            utils_models.LogEntry.objects.filter(
                types="File Access",
                description__contains="Embargoed until 1 January 2027",
            ).exists()
        )

    def test_an_embargo_needs_an_end_date(self):
        response = self.post({"access": "embargoed", "embargo_until": ""})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Give the date the embargo ends.")
        self.preprint_file.refresh_from_db()
        self.assertFalse(self.preprint_file.is_locked())

    def test_only_an_embargo_keeps_an_end_date(self):
        self.post({"access": "restricted", "embargo_until": "2027-01-01"})
        self.preprint_file.refresh_from_db()
        self.assertEqual(self.preprint_file.access, "restricted")
        self.assertIsNone(self.preprint_file.embargo_until)

    def test_readers_cannot_change_access(self):
        response = self.post({"access": "open"}, user=self.reader)
        self.assertNotEqual(response.status_code, 302)
        self.preprint_file.refresh_from_db()
        self.assertEqual(self.preprint_file.access, "open")

    def test_the_manager_page_shows_access_on_institutional_repositories_only(self):
        manager_url = reverse(
            "repository_manager_article", kwargs={"preprint_id": self.preprint.pk}
        )
        response = self.get(manager_url, user=self.manager)
        self.assertContains(response, self.url)
        self.repository.repository_type = rm.Repository.TYPE_PREPRINT_SERVER
        self.repository.save()
        response = self.get(manager_url, user=self.manager)
        self.assertNotContains(response, self.url)


@freeze_time("2026-11-11 12:00:00")
class SubmissionAccessTests(FileAccessTestBase):
    def setUp(self):
        super().setUp()
        self.draft = rm.Preprint.objects.create(
            repository=self.repository, owner=self.owner, title="A draft"
        )
        self.draft_file = rm.PreprintFile(
            preprint=self.draft,
            original_filename="aam.pdf",
            mime_type="application/pdf",
        )
        self.draft_file.file.save("aam.pdf", ContentFile(PDF), save=False)
        with mock.patch.object(rm.PreprintFile, "index_full_text"):
            self.draft_file.save()
        self.draft.submission_file = self.draft_file
        self.draft.save()
        self.url = reverse("repository_files", kwargs={"preprint_id": self.draft.pk})

    def test_a_depositor_embargoes_their_accepted_manuscript(self):
        self.client.force_login(self.owner)
        page = self.client.get(self.url, SERVER_NAME=self.repository.domain)
        self.assertContains(page, 'name="file_access"')
        self.client.post(
            self.url,
            {
                "file_access": "",
                "access": "embargoed",
                "embargo_until": "2027-06-01",
                "document_version": "accepted",
            },
            SERVER_NAME=self.repository.domain,
        )
        self.draft_file.refresh_from_db()
        self.assertEqual(self.draft_file.access, "embargoed")
        self.assertEqual(self.draft_file.embargo_until, datetime.date(2027, 6, 1))
        self.assertEqual(self.draft_file.document_version, "accepted")
        self.draft.refresh_from_db()
        self.assertEqual(self.draft.submission_file, self.draft_file)

    def test_preprint_servers_dont_ask(self):
        self.repository.repository_type = rm.Repository.TYPE_PREPRINT_SERVER
        self.repository.save()
        self.client.force_login(self.owner)
        page = self.client.get(self.url, SERVER_NAME=self.repository.domain)
        self.assertNotContains(page, 'name="file_access"')
