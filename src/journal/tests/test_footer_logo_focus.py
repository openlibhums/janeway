__copyright__ = "Copyright 2026 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from django.test import SimpleTestCase

from utils.testing import helpers


class OLHFooterLogoFocusTests(SimpleTestCase):
    def test_footer_logo_link_keeps_its_size_when_focused(self):
        scss = helpers.read_theme_asset("OLH", "assets/scss/app.scss")
        self.assertIn(
            "    a {\n"
            "      display: inline-block;\n"
            "    }\n"
            "\n"
            "    a svg {\n"
            "      display: block;\n"
            "      width: 180px;\n"
            "    }",
            scss,
        )
