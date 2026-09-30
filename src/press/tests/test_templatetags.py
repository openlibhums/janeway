__copyright__ = "Copyright 2026 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

import os
import shutil
import tempfile
from types import SimpleNamespace

from bs4 import BeautifulSoup
from django.test import SimpleTestCase

from press.templatetags import press_url

LOGO = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'
    "<title>Logo-Final</title><path/></svg>"
)

AWKWARD_FILES = {
    "byte order mark": "﻿" + LOGO,
    "illustrator doctype": (
        '<?xml version="1.0"?>\n<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" '
        '"http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd" '
        '[<!ENTITY ns_extend "http://ns.adobe.com/Extensibility/1.0/">]>\n' + LOGO
    ),
    "prefixed root": (
        '<svg:svg xmlns:svg="http://www.w3.org/2000/svg"><svg:path/></svg:svg>'
    ),
    "hidden root": LOGO.replace("<svg ", '<svg aria-hidden="true" '),
}


def image_name(rendered):
    """The accessible name of the rendered image, as role="img" gives it."""
    element = BeautifulSoup(rendered, "html.parser").find(attrs={"role": "img"})
    return element["aria-label"] if element else None


class SVGTagTests(SimpleTestCase):
    def setUp(self):
        self.directory = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.directory)
        self.path = self.write("logo.svg", LOGO)

    def write(self, name, content, encoding="utf-8"):
        path = os.path.join(self.directory, name)
        with open(path, "w", encoding=encoding) as f:
            f.write(content)
        return path

    def test_names_the_svg(self):
        rendered = press_url.svg(self.path, alt_text="Example Press")
        self.assertEqual(image_name(rendered), "Example Press")
        self.assertIn(LOGO, rendered)

    def test_names_awkward_files(self):
        for label, content in AWKWARD_FILES.items():
            with self.subTest(label):
                path = self.write(f"{label}.svg", content)
                rendered = press_url.svg(path, alt_text="Example Press")
                self.assertEqual(image_name(rendered), "Example Press")

    def test_undecodable_file_does_not_raise(self):
        path = self.write("latin1.svg", LOGO.replace("Logo", "Logó"), "latin-1")
        rendered = press_url.svg(path, alt_text="Example Press")
        self.assertEqual(image_name(rendered), "Example Press")

    def test_escapes_alt_text(self):
        rendered = press_url.svg(self.path, alt_text='Press " onload="alert(1)')
        self.assertIn('aria-label="Press &quot; onload=&quot;alert(1)"', rendered)

    def test_without_alt_text_is_decorative(self):
        rendered = press_url.svg(self.path)
        self.assertIsNone(image_name(rendered))
        self.assertIn('aria-hidden="true"', rendered)

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

    def test_inline_svg_is_named(self):
        rendered = press_url.svg_or_image(
            self.field, alt_text="Example Press", inline=True
        )
        self.assertEqual(image_name(rendered), "Example Press")
