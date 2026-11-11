from io import StringIO

from django.core import mail
from django.core.management import call_command
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time

from repository import models as rm
from submission import models as sm
from utils import models as utils_models
from utils.install import update_settings
from repository.tests.test_file_access import MARKER, PDF, FileAccessTestBase

REQUEST = {
    "name": "Rosa Reader",
    "email": "rosa@reader.example",
    "reason": "For my thesis on gravity priors.",
}


@freeze_time("2026-11-11 12:00:00")
@override_settings(
    CAPTCHA_TYPE="", EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"
)
class RequestCopyTests(FileAccessTestBase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        update_settings()  # the email settings

    def setUp(self):
        super().setUp()
        self.repository.request_copy = True
        self.repository.save()
        self.preprint, self.file = self.published_preprint(
            PDF, "aam.pdf", "application/pdf"
        )
        self.lock(self.file)
        self.file.document_version = rm.PreprintFile.VERSION_ACCEPTED
        self.file.save(update_fields=["document_version"])
        self.author = sm.FrozenAuthor.objects.create(
            preprint=self.preprint,
            first_name="Ada",
            last_name="Author",
            frozen_email="ada@author.example",
            order=0,
        )
        self.request_url = reverse(
            "repository_request_copy",
            kwargs={"preprint_id": self.preprint.pk, "file_id": self.file.pk},
        )
        mail.outbox = []

    def ask(self):
        self.client.logout()
        return self.client.post(
            self.request_url, REQUEST, SERVER_NAME=self.repository.domain
        )

    def post(self, url, data=None, user=None):
        if user:
            self.client.force_login(user)
        else:
            self.client.logout()
        return self.client.post(url, data or {}, SERVER_NAME=self.repository.domain)

    def decide_url(self, copy_request):
        return reverse(
            "repository_copy_request_decide", kwargs={"token": copy_request.token}
        )

    def download_url(self, copy_request):
        return reverse(
            "repository_copy_request_download",
            kwargs={"token": copy_request.download_token},
        )

    # When it's offered

    def test_offered_for_a_locked_accepted_manuscript(self):
        for theme in ("OLH", "material", "clarity"):
            with self.subTest(theme=theme):
                self.repository.theme = theme
                self.repository.save()
                self.assertContains(self.get(self.preprint.local_url), self.request_url)
                form_page = self.get(self.request_url)
                self.assertContains(form_page, "Send request")
                self.assertContains(form_page, 'name="reason"')

    def test_not_offered_otherwise(self):
        cases = (
            (
                "the setting is off",
                lambda: setattr(self.repository, "request_copy", False),
            ),
            (
                "it's a preprint server",
                lambda: setattr(
                    self.repository,
                    "repository_type",
                    rm.Repository.TYPE_PREPRINT_SERVER,
                ),
            ),
        )
        for label, change in cases:
            with self.subTest(label):
                change()
                self.repository.save()
                self.assertNotContains(
                    self.get(self.preprint.local_url), self.request_url
                )
                self.assertEqual(self.get(self.request_url).status_code, 404)
                self.repository.request_copy = True
                self.repository.repository_type = rm.Repository.TYPE_INSTITUTIONAL
                self.repository.save()

    def test_not_for_a_version_of_record_or_an_open_file(self):
        self.file.document_version = rm.PreprintFile.VERSION_PUBLISHED
        self.file.save(update_fields=["document_version"])
        self.assertEqual(self.get(self.request_url).status_code, 404)
        self.file.document_version = rm.PreprintFile.VERSION_ACCEPTED
        self.file.access = rm.PreprintFile.ACCESS_OPEN
        self.file.save(update_fields=["document_version", "access"])
        self.assertEqual(self.get(self.request_url).status_code, 404)

    # Asking

    def test_a_request_goes_to_the_chosen_author_without_showing_their_address(self):
        self.preprint.copy_request_author = self.author
        self.preprint.save()
        response = self.ask()
        self.assertRedirects(
            response, self.preprint.local_url, fetch_redirect_response=False
        )
        copy_request = rm.CopyRequest.objects.get()
        self.assertEqual(copy_request.asked_email, "ada@author.example")
        self.assertEqual(
            [message.to for message in mail.outbox], [["ada@author.example"]]
        )
        self.assertIn(self.decide_url(copy_request), mail.outbox[0].body)
        self.assertIn("thesis on gravity", mail.outbox[0].body)
        page = self.client.get(
            self.preprint.local_url, SERVER_NAME=self.repository.domain
        )
        self.assertNotContains(page, "ada@author.example")
        self.assertTrue(
            utils_models.LogEntry.objects.filter(types="Request a copy").exists()
        )

    def test_the_owner_is_asked_when_no_author_is_chosen(self):
        self.ask()
        self.assertEqual(rm.CopyRequest.objects.get().asked_email, self.owner.email)

    def test_the_form_needs_a_name_email_and_reason(self):
        response = self.client.post(
            self.request_url,
            {"email": "not an email"},
            SERVER_NAME=self.repository.domain,
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(rm.CopyRequest.objects.exists())

    # Answering

    def test_the_author_approves_and_the_reader_downloads_for_a_week(self):
        self.ask()
        copy_request = rm.CopyRequest.objects.get()
        decide = self.decide_url(copy_request)

        self.get(decide)  # looking changes nothing (mail systems follow links)
        copy_request.refresh_from_db()
        self.assertEqual(copy_request.status, rm.CopyRequest.STATUS_PENDING)

        self.post(decide, {"approve": ""})
        copy_request.refresh_from_db()
        self.assertEqual(copy_request.status, rm.CopyRequest.STATUS_APPROVED)
        self.assertIsNone(copy_request.decided_by)
        reader_email = mail.outbox[-1]
        self.assertEqual(reader_email.to, [REQUEST["email"]])
        self.assertIn(self.download_url(copy_request), reader_email.body)
        self.assertNotIn("ada@author.example", reader_email.body)
        self.assertNotIn(self.owner.email, reader_email.body)

        download = self.get(self.download_url(copy_request))
        self.assertEqual(download.status_code, 200)
        self.assertIn(MARKER.encode(), b"".join(download.streaming_content))
        copy_request.refresh_from_db()
        self.assertEqual(copy_request.downloads, 1)
        # The file itself stays locked to everyone else.
        self.assertEqual(self.get(self.download_url_for_file()).status_code, 403)

        with freeze_time("2026-11-19 12:00:00"):
            self.assertEqual(self.get(self.download_url(copy_request)).status_code, 404)

    def download_url_for_file(self):
        return reverse(
            "repository_file_download",
            kwargs={"preprint_id": self.preprint.pk, "file_id": self.file.pk},
        )

    def test_an_answer_is_given_once(self):
        self.ask()
        copy_request = rm.CopyRequest.objects.get()
        self.post(self.decide_url(copy_request), {"decline": ""})
        self.post(self.decide_url(copy_request), {"approve": ""})
        copy_request.refresh_from_db()
        self.assertEqual(copy_request.status, rm.CopyRequest.STATUS_DECLINED)
        self.assertIsNone(copy_request.download_token)
        self.assertEqual(mail.outbox[-1].to, [REQUEST["email"]])
        self.assertIn("can't be", mail.outbox[-1].body)

    def test_a_manager_answers_for_the_author(self):
        self.ask()
        copy_request = rm.CopyRequest.objects.get()
        list_url = reverse("repository_copy_requests")
        page = self.get(list_url, user=self.manager)
        self.assertContains(page, REQUEST["email"])
        self.post(
            list_url,
            {"copy_request": copy_request.pk, "approve": ""},
            user=self.manager,
        )
        copy_request.refresh_from_db()
        self.assertEqual(copy_request.status, rm.CopyRequest.STATUS_APPROVED)
        self.assertEqual(copy_request.decided_by, self.manager)

    def test_readers_cannot_see_the_list(self):
        response = self.get(reverse("repository_copy_requests"), user=self.reader)
        self.assertNotEqual(response.status_code, 200)

    # Expiry

    def test_unanswered_requests_expire_after_30_days(self):
        self.ask()
        copy_request = rm.CopyRequest.objects.get()
        with freeze_time("2026-12-12 12:00:00"):
            page = self.get(self.decide_url(copy_request))
            self.assertContains(page, "too late")
            self.post(self.decide_url(copy_request), {"approve": ""})
            copy_request.refresh_from_db()
            self.assertEqual(copy_request.status, rm.CopyRequest.STATUS_PENDING)

            mail.outbox = []
            call_command("expire_copy_requests", stdout=StringIO())
            copy_request.refresh_from_db()
            self.assertEqual(copy_request.status, rm.CopyRequest.STATUS_EXPIRED)
            self.assertEqual(
                [message.to for message in mail.outbox], [[REQUEST["email"]]]
            )

    # Choosing the author

    def test_a_manager_chooses_the_author_asked(self):
        url = reverse(
            "repository_copy_request_author", kwargs={"preprint_id": self.preprint.pk}
        )
        self.post(url, {"copy_request_author": self.author.pk}, user=self.manager)
        self.preprint.refresh_from_db()
        self.assertEqual(self.preprint.copy_request_author, self.author)

        no_email = sm.FrozenAuthor.objects.create(
            preprint=self.preprint, first_name="No", last_name="Email", order=1
        )
        self.post(url, {"copy_request_author": no_email.pk}, user=self.manager)
        self.preprint.refresh_from_db()
        self.assertEqual(self.preprint.copy_request_author, self.author)

        self.post(url, {"copy_request_author": ""}, user=self.manager)
        self.preprint.refresh_from_db()
        self.assertIsNone(self.preprint.copy_request_author)

    def test_another_preprints_author_cannot_be_chosen(self):
        other, _file = self.published_preprint(
            PDF, "other.pdf", "application/pdf", title="Other"
        )
        stranger = sm.FrozenAuthor.objects.create(
            preprint=other,
            first_name="S",
            last_name="Tranger",
            frozen_email="s@tranger.example",
            order=0,
        )
        url = reverse(
            "repository_copy_request_author", kwargs={"preprint_id": self.preprint.pk}
        )
        self.post(url, {"copy_request_author": stranger.pk}, user=self.manager)
        self.preprint.refresh_from_db()
        self.assertIsNone(self.preprint.copy_request_author)
