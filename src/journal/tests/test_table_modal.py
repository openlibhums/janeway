__copyright__ = "Copyright 2026 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from unittest import mock

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from utils import setting_handler
from utils.shared import clear_cache
from utils.testing import helpers

GALLEY_WITH_TABLE = """
<div class="table-expansion" id="T1">
  <table><caption><span class="table-label" id="T1-label">Table 1</span></caption>
    <tr><td>Cell<a class="xref-table-fn" href="#TF1" id="TF1-nm1"><sup>a</sup></a></td></tr>
  </table>
  <ol class="table-footnotes"><li id="TF1">A footnote.</li></ol>
</div>
"""


@override_settings(URL_CONFIG="domain")
class TableModalRequestTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.press = helpers.create_press()
        cls.journal_one, cls.journal_two = helpers.create_journals()
        setting_handler.save_setting(
            "general",
            "journal_theme",
            cls.journal_one,
            "clean",
        )
        cls.article = helpers.create_article(
            journal=cls.journal_one,
            stage="Published",
            date_published=timezone.now() - timezone.timedelta(days=1),
        )
        cls.article.render_galley = helpers.create_galley(
            cls.article,
            type="html",
            public=True,
        )
        cls.article.save()

    def setUp(self):
        clear_cache()

    @mock.patch("core.models.Galley.file_content", return_value=GALLEY_WITH_TABLE)
    def test_clean_table_modal_can_take_focus(self, file_content):
        response = self.client.get(
            reverse(
                "article_view",
                kwargs={"identifier_type": "id", "identifier": self.article.pk},
            ),
            SERVER_NAME=self.journal_one.domain,
        )
        self.assertContains(
            response,
            '<div class="modal " id="table-T1" tabindex="-1" role="dialog" '
            'aria-labelledby="copy-of-T1-label">',
        )
        self.assertContains(response, 'href="#copy-of-TF1"')
