__copyright__ = "Copyright 2024 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from unittest import mock

from django.contrib.contenttypes.models import ContentType
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from core import models as core_models
from core.logic import reverse_with_query
from submission import models as submission_models
from utils import models as utils_models
from utils.testing import helpers


class JournalViewTestsWithData(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.editor_one = helpers.create_editor(
            cls.journal_one,
            email="editor_jiqjgaysqge1pahnj4xn@example.org",
            first_name="Editor",
            last_name="One",
        )
        cls.editor_two = helpers.create_editor(
            cls.journal_one,
            email="editor_iw9pm21rrrxhm9kp5rfa@example.org",
            first_name="Editor",
            last_name="Two",
        )
        cls.contact_person_one = helpers.create_contact_person(
            cls.editor_one,
            cls.journal_one,
        )
        cls.contact_person_two = helpers.create_contact_person(
            cls.editor_two,
            cls.journal_one,
        )
        cls.journal_content_type = ContentType.objects.get_for_model(cls.journal_one)
        cls.sections = []
        cls.articles = []
        thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
        for section_name in ["Article", "Review", "Comment", "Editorial"]:
            section = helpers.create_section(
                journal=cls.journal_one,
                name=section_name,
            )
            cls.sections.append(section)
            for num in range(1, 16):
                cls.articles.append(
                    helpers.create_article(
                        journal=cls.journal_one,
                        title=f"{section_name} {num}",
                        section=section,
                        stage="Published",
                        date_published=thirty_days_ago,
                    )
                )


class PublishedArticlesListViewTests(JournalViewTestsWithData):
    def setUp(self):
        self.client = Client()

    def test_count_no_filters(self):
        data = {}
        response = self.client.get("/articles/", data)
        self.assertIn(
            "60 results",
            response.content.decode(),
        )

    def test_count_filtered_on_section(self):
        data = {"section__pk": self.sections[0].pk}
        response = self.client.get("/articles/", data)
        self.assertIn(
            "15 results",
            response.content.decode(),
        )

    def test_counts_match_with_filters(self):
        data = {
            "section__pk": self.sections[0].pk,
        }
        response = self.client.get("/articles/", data)
        self.assertIn(
            "15 results",
            response.content.decode(),
        )
        self.assertIn(
            "Article (15)",
            response.content.decode(),
        )


class JournalContactTests(JournalViewTestsWithData):
    @override_settings(URL_CONFIG="domain")
    def test_contact_GET(self):
        response = self.client.get(
            reverse("contact"),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertEqual(
            self.contact_person_one.account.email,
            response.context["contacts"][0].account.email,
        )
        self.assertEqual(
            [
                (self.contact_person_one.pk, self.editor_one.full_name()),
                (self.contact_person_two.pk, self.editor_two.full_name()),
            ],
            response.context["contact_form"].fields["contact_person"].choices,
        )

    @override_settings(URL_CONFIG="domain")
    def test_journal_contact_with_recipient_GET(self):
        url = reverse(
            "journal_contact_with_recipient",
            kwargs={"contact_person_id": self.contact_person_two.pk},
        )
        response = self.client.get(url, SERVER_NAME=self.journal_one.domain)
        self.assertEqual(
            self.contact_person_two.pk,
            response.context["contact_form"].fields["contact_person"].initial,
        )

    @override_settings(URL_CONFIG="domain")
    @override_settings(CAPTCHA_TYPE="")
    def test_contact_POST(self):
        post_data = {
            "contact_person": self.contact_person_one.pk,
            "sender": "santa@example.org",
            "subject": "Merry Christmas",
            "body": "Tis the season\nTo be jolly",
        }
        self.client.post(
            reverse("contact"),
            post_data,
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertTrue(
            utils_models.LogEntry.objects.filter(
                actor_email="santa@example.org",
                content_type=self.journal_content_type,
                object_id=self.journal_one.pk,
            ).exists()
        )

    @override_settings(URL_CONFIG="domain")
    def test_contact_GET_announces_required_message_body(self):
        response = self.client.get(
            reverse("contact"),
            SERVER_NAME=self.journal_one.domain,
        )
        content = response.content.decode()
        self.assertIn('aria-required="true"', content)

    @override_settings(URL_CONFIG="domain")
    def test_contact_GET_body_is_plain_textarea(self):
        from django import forms as django_forms
        from tinymce.widgets import TinyMCE

        response = self.client.get(
            reverse("contact"),
            SERVER_NAME=self.journal_one.domain,
        )
        widget = response.context["contact_form"].fields["body"].widget
        self.assertNotIsInstance(widget, TinyMCE)
        self.assertIsInstance(widget, django_forms.Textarea)

    @override_settings(URL_CONFIG="domain")
    @override_settings(CAPTCHA_TYPE="")
    def test_contact_POST_email_names_journal_and_press(self):
        from django.core import mail

        post_data = {
            "contact_person": self.contact_person_one.pk,
            "sender": "santa@example.org",
            "subject": "Where am I from?",
            "body": "A message of unclear provenance.",
        }
        self.client.post(
            reverse("contact"),
            post_data,
            SERVER_NAME=self.journal_one.domain,
        )
        message = mail.outbox[-1]
        self.assertIn(self.journal_one.name, message.body)
        self.assertIn(self.press.name, message.body)

    @override_settings(URL_CONFIG="domain")
    @override_settings(CAPTCHA_TYPE="")
    def test_contact_invalid_POST_error_summary(self):
        post_data = {
            "contact_person": self.contact_person_one.pk,
            "sender": "not-an-email-address",
            "subject": "Merry Christmas",
            "body": "",
        }
        response = self.client.post(
            reverse("contact"),
            post_data,
            SERVER_NAME=self.journal_one.domain,
        )
        content = response.content.decode()
        self.assertIn('id="form-errors-heading"', content)
        self.assertIn('aria-labelledby="form-errors-heading"', content)
        self.assertIn("There is a problem with the form", content)
        self.assertIn("<dl>", content)
        self.assertIn('<a href="#id_sender">', content)
        self.assertIn('<a href="#id_body">', content)
        self.assertIn(
            "Provide a valid email address in the format name@domain.com.",
            content,
        )
        self.assertIn(
            "Enter the message you would like to send.",
            content,
        )


class ArticleDownloadAccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.under_review = helpers.create_article(
            cls.journal_one,
            stage=submission_models.STAGE_UNDER_REVIEW,
        )
        cls.accepted = helpers.create_article(
            cls.journal_one,
            stage=submission_models.STAGE_ACCEPTED,
        )
        xml_file = core_models.File.objects.create(
            article_id=cls.accepted.pk,
            label="XML",
            mime_type="application/xml",
            uuid_filename="article.xml",
        )
        helpers.create_galley(cls.accepted, file_obj=xml_file)

    def download(self, url_name, identifier):
        return self.client.get(
            reverse(
                url_name,
                kwargs={"identifier_type": "id", "identifier": identifier},
            ),
            SERVER_NAME=self.journal_one.domain,
        )

    @override_settings(URL_CONFIG="domain")
    def test_xml_not_served_for_unpublished_article(self):
        response = self.download("serve_article_xml", self.accepted.pk)
        self.assertEqual(response.status_code, 404)

    @override_settings(URL_CONFIG="domain")
    def test_citation_downloads_refused_before_acceptance(self):
        for url_name in ("serve_article_ris", "serve_article_bib"):
            with self.subTest(url_name=url_name):
                response = self.download(url_name, self.under_review.pk)
                self.assertEqual(response.status_code, 403)


@override_settings(URL_CONFIG="domain")
class FileDeleteTests(TestCase):
    """The file delete view asks for confirmation and only deletes on POST."""

    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        cls.editor = helpers.create_editor(
            cls.journal_one,
            email="editor_file_delete@example.org",
        )
        cls.regular_user = helpers.create_regular_user()
        cls.article = helpers.create_article(cls.journal_one)

    def setUp(self):
        self.file = core_models.File.objects.create(
            article_id=self.article.pk,
            label="Manuscript",
            original_filename="manuscript.docx",
            uuid_filename="file-delete-test.docx",
            owner=self.editor,
        )
        self.delete_url = reverse(
            "file_delete",
            kwargs={"article_id": self.article.pk, "file_id": self.file.pk},
        )
        self.return_url = reverse(
            "document_management", kwargs={"article_id": self.article.pk}
        )
        self.client.force_login(self.editor)

        # No test file is written to disk, so stub out the unlinking of the
        # stored copy. This keeps the tests off the real files directory and
        # stops File.unlink_file printing "file_not_found".
        patcher = mock.patch.object(core_models.File, "unlink_file")
        self.unlink_file = patcher.start()
        self.addCleanup(patcher.stop)

    def get(self, url):
        return self.client.get(url, SERVER_NAME=self.journal_one.domain)

    def post(self, url):
        return self.client.post(url, SERVER_NAME=self.journal_one.domain)

    def file_exists(self):
        return core_models.File.objects.filter(pk=self.file.pk).exists()

    def test_get_shows_confirmation_and_does_not_delete(self):
        response = self.get(f"{self.delete_url}?return={self.return_url}")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin/journal/file_delete.html")
        self.assertContains(response, "manuscript.docx")
        self.assertTrue(self.file_exists())
        self.unlink_file.assert_not_called()

    def test_get_without_return_does_not_error_or_delete(self):
        response = self.get(self.delete_url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.file_exists())

    def cancel_link(self, href):
        return f'<a href="{href}" class="button no-bottom-margin">'

    def test_cancel_link_points_to_return_url(self):
        response = self.get(f"{self.delete_url}?return={self.return_url}")
        self.assertContains(response, self.cancel_link(self.return_url))

    def test_cancel_link_falls_back_when_return_is_unsafe(self):
        for unsafe in ("", "https://evil.example.com/", "//evil.example.com/"):
            with self.subTest(return_url=unsafe):
                response = self.get(f"{self.delete_url}?return={unsafe}")
                self.assertContains(response, self.cancel_link(self.return_url))
                # The page chrome echoes the request URL in hidden fields, so
                # only check that nothing links off-site.
                self.assertNotContains(response, 'href="https://evil.example.com')
                self.assertNotContains(response, 'href="//evil.example.com')

    def test_following_cancel_link_keeps_file(self):
        response = self.get(f"{self.delete_url}?return={self.return_url}")
        self.assertContains(response, self.cancel_link(self.return_url))
        response = self.get(self.return_url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.file_exists())
        self.unlink_file.assert_not_called()

    def test_post_deletes_file_and_redirects_to_return(self):
        response = self.post(f"{self.delete_url}?return={self.return_url}")
        self.assertRedirects(response, self.return_url, fetch_redirect_response=False)
        self.assertFalse(self.file_exists())
        self.unlink_file.assert_called_once()

    def test_post_without_return_falls_back_to_document_management(self):
        response = self.post(self.delete_url)
        self.assertRedirects(response, self.return_url, fetch_redirect_response=False)
        self.assertFalse(self.file_exists())

    def test_unsafe_return_url_is_ignored(self):
        for unsafe in ("https://evil.example.com/", "//evil.example.com/"):
            with self.subTest(return_url=unsafe):
                file = core_models.File.objects.create(
                    article_id=self.article.pk,
                    original_filename="other.docx",
                    uuid_filename="file-delete-other.docx",
                    owner=self.editor,
                )
                url = reverse(
                    "file_delete",
                    kwargs={"article_id": self.article.pk, "file_id": file.pk},
                )
                response = self.post(f"{url}?return={unsafe}")
                self.assertRedirects(
                    response, self.return_url, fetch_redirect_response=False
                )

    def test_post_writes_log_entry(self):
        file_pk = self.file.pk
        self.post(f"{self.delete_url}?return={self.return_url}")
        entry = utils_models.LogEntry.objects.get(types="File Deleted")
        self.assertEqual(entry.actor, self.editor)
        self.assertEqual(entry.target, self.article)
        self.assertIn(str(file_pk), entry.description)
        self.assertIn("manuscript.docx", entry.description)
        self.assertIn("file-delete-test.docx", entry.description)
        self.assertIn(self.editor.username, entry.description)

    def test_get_writes_no_log_entry(self):
        self.get(self.delete_url)
        self.assertFalse(
            utils_models.LogEntry.objects.filter(types="File Deleted").exists()
        )

    def test_user_without_permission_cannot_delete(self):
        self.client.force_login(self.regular_user)
        for method in (self.get, self.post):
            with self.subTest(method=method.__name__):
                response = method(self.delete_url)
                self.assertNotEqual(response.status_code, 200)
                self.assertTrue(self.file_exists())
        self.unlink_file.assert_not_called()
        self.assertFalse(
            utils_models.LogEntry.objects.filter(types="File Deleted").exists()
        )

    def test_replace_page_delete_param_redirects_to_confirmation(self):
        url = reverse(
            "article_file_replace",
            kwargs={
                "identifier_type": "id",
                "identifier": self.article.pk,
                "file_id": self.file.pk,
            },
        )
        response = self.get(f"{url}?delete=1")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(self.delete_url))
        self.assertIn("return=", response.url)
        self.assertTrue(self.file_exists())
