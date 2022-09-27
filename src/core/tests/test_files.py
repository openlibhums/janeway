import os
import shutil
from tempfile import NamedTemporaryFile

from django.urls import reverse
from django.urls.base import clear_script_prefix
from django.test import TestCase, Client, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.utils import timezone
import pdfkit

from utils.testing import helpers
from utils.shared import clear_cache
from submission import models as submission_models
from core import files


class TestFilesHandler(TestCase):

    def setUp(self):
        self.press = helpers.create_press()
        self.press.save()
        self.journal_one, self.journal_two = helpers.create_journals()

        self.regular_user = helpers.create_user("harrykim@voyager.com")
        self.regular_user.is_active = True
        self.regular_user.save()

        self.article_in_production = submission_models.Article.objects.create(
            owner=self.regular_user, title="A Test Article",
            abstract="An abstract",
            stage=submission_models.STAGE_TYPESETTING,
            journal=self.journal_one,
            date_accepted=timezone.now(),
        )
        self.pk_string = str(self.article_in_production.pk)
        self.request = helpers.Request()
        self.request.user = self.regular_user

        self.test_file_one = SimpleUploadedFile(
            "test.png",
            b"\x00\x01\x02\x03",
        )

        self.test_file_two = SimpleUploadedFile(
            "file.txt",
            b"content",
        )
        self.test_xml_file = SimpleUploadedFile(
            "test.xml",
            """
            <?xml version="1.0" encoding="UTF-8"?>
            <!DOCTYPE article PUBLIC "-//NLM//DTD JATS (Z39.96) Journal Publishing DTD v1.2 20120330//EN" "http://jats.nlm.nih.gov/publishing/1.2/JATS-journalpublishing1.dtd">
            <article>test</article>
            """.strip().encode("utf-8"),
        )

        self.files = list()

    def tearDown(self):
        for file in self.files:
            os.unlink(
                os.path.join(
                    settings.BASE_DIR,
                    'files',
                    'articles',
                    self.pk_string,
                    file.uuid_filename,
                )
            )

    def test_save_file(self):
        helpers.create_test_file(self, self.test_file_one)

        expected_file_path = os.path.join(
            os.path.join(
                settings.BASE_DIR, 'files', 'articles', self.pk_string,
            )
        )

        file_check = os.path.exists(
            expected_file_path,
        )

        self.assertTrue(file_check)

    def test_overwrite_file(self):
        file_to_replace, path_parts = helpers.create_test_file(
            self,
            self.test_file_one,
        )

        files.overwrite_file(
            self.test_file_two,
            file_to_replace,
            path_parts=path_parts,
        )

        file_path = os.path.join(
            settings.BASE_DIR,
            'files',
            'articles',
            self.pk_string,
            file_to_replace.uuid_filename,
        )

        with open(file_path, 'rb') as file:
            content = file.read()
            self.assertEqual(content, b'content')

    @override_settings(URL_CONFIG='domain')
    def test_serve_any_file(self):

        file, path_parts = helpers.create_test_file(
            self,
            self.test_file_two,
        )

        clear_cache()
        clear_script_prefix()

        url = reverse(
            'article_file_download',
            kwargs={
                'identifier_type': 'id',
                'identifier': self.article_in_production.pk,
                'file_id': file.pk,
            }
        )

        self.client.force_login(self.regular_user)
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_xml_to_text(self):
        with NamedTemporaryFile("wb") as f:
            f.write(self.test_xml_file.read())
            f.seek(0)
            parsed_text = files.jats_to_text(f.name).strip()

        expected = "test"

        self.assertEqual(parsed_text, expected)

    def test_pdf_to_text(self):
        with NamedTemporaryFile("r+b") as f:
            # Write a PDF File
            text = "Hello World"
            config = pdfkit.configuration(wkhtmltopdf=os.path.join(
                settings.BASE_DIR,
                'transform/cassius/bin/wkhtmltopdf'
            ))
            pdfkit.from_string(text, output_path=f.name, configuration=config)

            # Parse the PDF File
            parsed_text = files.pdf_to_text(f.name).strip()


        self.assertEqual(parsed_text, text)

    def test_index_file(self):
        file_ = files.save_file_to_article(
            self.test_xml_file,
            article=self.article_in_production,
            owner=self.request.user,
            label="test-xml",
        )
        indexed = file_.index_full_text()

        self.assertTrue(indexed)

