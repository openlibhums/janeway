import os
import re
from tempfile import NamedTemporaryFile

from django.urls import reverse
from django.urls.base import clear_script_prefix
from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.utils import timezone
from lxml import etree
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
            owner=self.regular_user,
            title="A Test Article",
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
                    "files",
                    "articles",
                    self.pk_string,
                    file.uuid_filename,
                )
            )

    def test_save_file(self):
        helpers.create_test_file(self, self.test_file_one)

        expected_file_path = os.path.join(
            os.path.join(
                settings.BASE_DIR,
                "files",
                "articles",
                self.pk_string,
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
            "files",
            "articles",
            self.pk_string,
            file_to_replace.uuid_filename,
        )

        with open(file_path, "rb") as file:
            content = file.read()
            self.assertEqual(content, b"content")

    @override_settings(URL_CONFIG="domain")
    def test_serve_any_file(self):
        file, path_parts = helpers.create_test_file(
            self,
            self.test_file_two,
        )

        clear_cache()
        clear_script_prefix()

        url = reverse(
            "article_file_download",
            kwargs={
                "identifier_type": "id",
                "identifier": self.article_in_production.pk,
                "file_id": file.pk,
            },
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
            config = pdfkit.configuration(
                wkhtmltopdf=os.path.join(
                    settings.BASE_DIR, "transform/cassius/bin/wkhtmltopdf"
                )
            )
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


class TestDefaultXSLTransform(TestCase):
    """Tests for the builtin default.xsl article rendering stylesheet."""

    @classmethod
    def setUpTestData(cls):
        cls.transform = etree.XSLT(etree.parse(settings.BUILTIN_XSL_PATH))

    def render(self, xml):
        return str(self.transform(etree.fromstring(xml.encode("utf-8"))))

    def test_ext_link_in_mixed_citation_not_duplicated(self):
        """An ext-link in a mixed-citation renders exactly one anchor (#4335)."""
        uri = "https://olh.openlibhums.org/article/id/4400/"
        doi = "https://doi.org/10.16995/olh.46"
        xml = (
            '<article xmlns:xlink="http://www.w3.org/1999/xlink"><back>'
            '<ref-list><ref id="R97"><mixed-citation publication-type="other">'
            "Wu, S. (2021). Retrieved from "
            '<ext-link ext-link-type="uri" xlink:href="{uri}">{uri}</ext-link>. '
            '<ext-link ext-link-type="doi" xlink:href="{doi}">{doi}</ext-link>'
            "</mixed-citation></ref></ref-list></back></article>"
        ).format(uri=uri, doi=doi)

        output = self.render(xml)

        self.assertEqual(output.count('<a href="{}"'.format(uri)), 1)
        self.assertEqual(output.count('<a href="{}"'.format(doi)), 1)

    def render_images(self, body):
        """Renders a JATS body fragment and returns each <img>'s alt."""
        output = self.render(
            '<article xmlns:xlink="http://www.w3.org/1999/xlink">'
            "<body><sec>{}</sec></body></article>".format(body)
        )
        alts = [
            re.search(r'alt="([^"]*)"', img).group(1) if "alt=" in img else None
            for img in re.findall(r"<img\b[^>]*>", output)
        ]
        return alts, re.sub(r"<[^>]+>", " ", output)

    def test_inline_graphic_uses_its_alt_text(self):
        alts, _ = self.render_images(
            '<p><inline-graphic xlink:href="i.png">'
            "<alt-text>Plus sign</alt-text></inline-graphic></p>"
        )
        self.assertEqual(alts, ["Plus sign"])

    def test_inline_graphic_without_alt_text_has_empty_alt(self):
        alts, _ = self.render_images('<p><inline-graphic xlink:href="i.png"/></p>')
        self.assertEqual(alts, [""])

    def test_graphic_uses_its_alt_text_and_does_not_show_it(self):
        alts, text = self.render_images(
            '<p><graphic xlink:href="g.png"><alt-text>A map of Leeds</alt-text>'
            "<caption>Map</caption></graphic></p>"
        )
        self.assertEqual(alts, ["A map of Leeds"])
        self.assertNotIn("A map of Leeds", text)

    def test_graphic_without_alt_text_uses_its_caption(self):
        alts, _ = self.render_images(
            '<p><graphic xlink:href="g.png"><caption>Map</caption></graphic></p>'
        )
        self.assertEqual(alts, ["Map"])

    def test_figure_uses_alt_text_on_the_graphic_or_the_figure(self):
        for body in [
            '<fig id="f1"><label>Figure 1</label><graphic xlink:href="f.png">'
            "<alt-text>Bar chart of sales</alt-text></graphic></fig>",
            '<fig id="f1"><label>Figure 1</label>'
            "<alt-text>Bar chart of sales</alt-text>"
            '<graphic xlink:href="f.png"/></fig>',
        ]:
            with self.subTest(body=body):
                alts, _ = self.render_images(body)
                self.assertEqual(alts, ["Bar chart of sales"])

    def test_figure_without_alt_text_uses_its_label(self):
        alts, _ = self.render_images(
            '<fig id="f1"><label>Figure 1</label><graphic xlink:href="f.png"/></fig>'
        )
        self.assertEqual(alts, ["Figure 1"])

    def test_table_image_uses_the_table_alt_text_and_does_not_show_it(self):
        alts, text = self.render_images(
            '<table-wrap id="t1"><label>Table 1</label>'
            "<alt-text>Scanned table of results</alt-text>"
            '<caption><p>Results</p></caption><graphic xlink:href="t.png"/>'
            "</table-wrap>"
        )
        self.assertEqual(alts, ["Scanned table of results"])
        self.assertNotIn("Scanned table of results", text)

    def test_figure_group_images_use_alt_text_then_labels(self):
        alts, _ = self.render_images(
            '<fig-group><fig id="a"><label>Figure 2</label>'
            '<graphic xlink:href="a.png"><alt-text>Map of sites</alt-text></graphic>'
            '</fig><fig id="b" specific-use="child"><label>Figure 2b</label>'
            '<graphic xlink:href="b.png"/></fig></fig-group>'
        )
        self.assertIn("Map of sites", alts)
        self.assertIn("Figure 2b", alts)
        self.assertNotIn("Figure 2", alts)
