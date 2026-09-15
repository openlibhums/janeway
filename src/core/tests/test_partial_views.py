__copyright__ = "Copyright 2026 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.shortcuts import reverse
from django.test import Client, TestCase, override_settings

from utils.testing import helpers


# Minimal valid 1x1 GIF, used as a stand-in image across upload tests.
# Taken from core/tests/test_models.py which confirms it passes SVGImageField
# validation.
MINIMAL_GIF = (
    b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04"
    b"\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02"
    b"\x02\x4c\x01\x00\x3b"
)


class JournalImageSettingsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        helpers.create_roles(["editor"])
        cls.editor = helpers.create_user(
            "editor_img_settings@example.org",
            roles=["editor"],
            journal=cls.journal_one,
        )
        cls.editor.is_active = True
        cls.editor.save()

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.editor)
        self.media_root = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.media_root, ignore_errors=True)

    def _image_file(self, name="test.gif"):
        return SimpleUploadedFile(name, MINIMAL_GIF, content_type="image/gif")

    # --- Settings page ---

    @override_settings(URL_CONFIG="domain")
    def test_images_settings_page_loads(self):
        url = reverse("core_edit_settings_group", kwargs={"display_group": "images"})
        response = self.client.get(url, SERVER_NAME=self.journal_one.domain)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin/core/manager/settings/group.html")

    @override_settings(URL_CONFIG="domain")
    def test_images_settings_page_requires_login(self):
        self.client.logout()
        url = reverse("core_edit_settings_group", kwargs={"display_group": "images"})
        response = self.client.get(url, SERVER_NAME=self.journal_one.domain)
        self.assertNotEqual(response.status_code, 200)

    # --- Upload view ---

    @override_settings(URL_CONFIG="domain")
    def test_image_upload_requires_post(self):
        url = reverse("journal_image_upload", kwargs={"field_name": "header_image"})
        response = self.client.get(url, SERVER_NAME=self.journal_one.domain)
        self.assertEqual(response.status_code, 405)

    @override_settings(URL_CONFIG="domain")
    def test_image_upload_rejects_invalid_field(self):
        url = reverse("journal_image_upload", kwargs={"field_name": "not_a_real_field"})
        response = self.client.post(url, {}, SERVER_NAME=self.journal_one.domain)
        self.assertEqual(response.status_code, 400)

    @override_settings(URL_CONFIG="domain")
    def test_image_upload_requires_login(self):
        self.client.logout()
        url = reverse("journal_image_upload", kwargs={"field_name": "header_image"})
        response = self.client.post(
            url,
            {"header_image": self._image_file()},
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertNotEqual(response.status_code, 200)

    @override_settings(URL_CONFIG="domain")
    def test_image_upload_saves_image(self):
        url = reverse("journal_image_upload", kwargs={"field_name": "header_image"})
        with override_settings(MEDIA_ROOT=self.media_root):
            response = self.client.post(
                url,
                {"header_image": self._image_file()},
                SERVER_NAME=self.journal_one.domain,
            )
        self.assertEqual(response.status_code, 200)
        self.journal_one.refresh_from_db()
        self.assertTrue(self.journal_one.header_image)

    @override_settings(URL_CONFIG="domain")
    def test_image_upload_returns_partial_template(self):
        url = reverse("journal_image_upload", kwargs={"field_name": "header_image"})
        with override_settings(MEDIA_ROOT=self.media_root):
            response = self.client.post(
                url,
                {"header_image": self._image_file()},
                SERVER_NAME=self.journal_one.domain,
            )
        self.assertTemplateUsed(
            response,
            "admin/core/partials/journal_image/upload_field.html",
        )

    @override_settings(URL_CONFIG="domain")
    def test_image_upload_returns_hx_trigger(self):
        url = reverse("journal_image_upload", kwargs={"field_name": "header_image"})
        with override_settings(MEDIA_ROOT=self.media_root):
            response = self.client.post(
                url,
                {"header_image": self._image_file()},
                SERVER_NAME=self.journal_one.domain,
            )
        self.assertIn("showMessage", response["HX-Trigger"])

    # --- Remove view ---

    @override_settings(URL_CONFIG="domain")
    def test_image_remove_requires_post(self):
        url = reverse("journal_image_remove", kwargs={"field_name": "header_image"})
        response = self.client.get(url, SERVER_NAME=self.journal_one.domain)
        self.assertEqual(response.status_code, 405)

    @override_settings(URL_CONFIG="domain")
    def test_image_remove_rejects_invalid_field(self):
        url = reverse("journal_image_remove", kwargs={"field_name": "not_a_real_field"})
        response = self.client.post(url, {}, SERVER_NAME=self.journal_one.domain)
        self.assertEqual(response.status_code, 400)

    @override_settings(URL_CONFIG="domain")
    def test_image_remove_clears_field(self):
        with override_settings(MEDIA_ROOT=self.media_root):
            self.journal_one.header_image.save(
                "test.gif",
                self._image_file(),
                save=True,
            )
            url = reverse("journal_image_remove", kwargs={"field_name": "header_image"})
            response = self.client.post(url, {}, SERVER_NAME=self.journal_one.domain)
        self.assertEqual(response.status_code, 200)
        self.journal_one.refresh_from_db()
        self.assertFalse(self.journal_one.header_image)

    @override_settings(URL_CONFIG="domain")
    def test_image_remove_returns_partial_template(self):
        with override_settings(MEDIA_ROOT=self.media_root):
            self.journal_one.header_image.save(
                "test.gif",
                self._image_file(),
                save=True,
            )
            url = reverse("journal_image_remove", kwargs={"field_name": "header_image"})
            response = self.client.post(url, {}, SERVER_NAME=self.journal_one.domain)
        self.assertTemplateUsed(
            response,
            "admin/core/partials/journal_image/upload_field.html",
        )

    @override_settings(URL_CONFIG="domain")
    def test_image_remove_returns_hx_trigger(self):
        with override_settings(MEDIA_ROOT=self.media_root):
            self.journal_one.header_image.save(
                "test.gif",
                self._image_file(),
                save=True,
            )
            url = reverse("journal_image_remove", kwargs={"field_name": "header_image"})
            response = self.client.post(url, {}, SERVER_NAME=self.journal_one.domain)
        self.assertIn("showMessage", response["HX-Trigger"])
