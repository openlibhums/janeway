__copyright__ = "Copyright 2026 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

import os
import shutil
import tempfile
from types import SimpleNamespace

from django.test import SimpleTestCase

from press.templatetags import press_url

LOGO = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    "<!-- Exported from an <svg> editor -->\n"
    '<svg xmlns="http://www.w3.org/2000/svg" role="presentation">'
    "<title>Logo-Final</title><path/></svg>"
)


class SVGTagTests(SimpleTestCase):
    def setUp(self):
        self.directory = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.directory)
        self.path = self.write("logo.svg", LOGO)

    def write(self, name, content):
        path = os.path.join(self.directory, name)
        with open(path, "w") as f:
            f.write(content)
        return path

    def test_labels_the_root_element(self):
        rendered = press_url.svg(self.path, alt_text="Example Press")
        self.assertIn(
            '<svg role="img" aria-label="Example Press" '
            'xmlns="http://www.w3.org/2000/svg" role="presentation">',
            rendered,
        )
        self.assertIn("<!-- Exported from an <svg> editor -->", rendered)

    def test_escapes_alt_text(self):
        rendered = press_url.svg(self.path, alt_text='Press " onload="alert(1)')
        self.assertIn('aria-label="Press &quot; onload=&quot;alert(1)"', rendered)

    def test_without_alt_text_leaves_the_file_unchanged(self):
        self.assertEqual(press_url.svg(self.path), LOGO)

    def test_rereads_a_replaced_file(self):
        press_url.svg(self.path, alt_text="Example Press")
        self.write("logo.svg", LOGO.replace("Logo-Final", "New logo"))
        stat = os.stat(self.path)
        os.utime(self.path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000))
        self.assertIn("New logo", press_url.svg(self.path, alt_text="Example Press"))

    def test_missing_file_renders_nothing(self):
        self.assertIsNone(press_url.svg(os.path.join(self.directory, "gone.svg")))

    def test_other_file_types_render_an_img_with_alt(self):
        rendered = press_url.svg("files/press/cover.png", alt_text='A "logo"')
        self.assertIn('alt="A &quot;logo&quot;"', rendered)
        self.assertTrue(rendered.startswith("<img "))


class SVGOrImageTagTests(SimpleTestCase):
    def setUp(self):
        directory = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, directory)
        self.path = os.path.join(directory, "logo.svg")
        with open(self.path, "w") as f:
            f.write(LOGO)
        self.field = SimpleNamespace(path=self.path, url="/media/logo.svg")

    def test_escapes_alt_text(self):
        rendered = press_url.svg_or_image(
            self.field, alt_text='Cover " onerror="alert(1)'
        )
        self.assertEqual(
            rendered,
            '<img src="/media/logo.svg" class="" '
            'alt="Cover &quot; onerror=&quot;alert(1)">',
        )

    def test_inline_svg_is_labelled(self):
        rendered = press_url.svg_or_image(
            self.field, alt_text="Example Press", inline=True
        )
        self.assertIn('<svg role="img" aria-label="Example Press" ', rendered)
