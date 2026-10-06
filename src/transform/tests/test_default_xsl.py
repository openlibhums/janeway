from django.conf import settings
from django.test import SimpleTestCase

from lxml import etree


JATS_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<article xmlns:xlink="http://www.w3.org/1999/xlink" article-type="research-article">
  <back>
    <ref-list>
      {title}
      <ref id="ref1">
        <element-citation publication-type="journal">
          <article-title>A cited work</article-title>
          <year>2020</year>
        </element-citation>
      </ref>
    </ref-list>
  </back>
</article>
"""


class TestRefListTransform(SimpleTestCase):
    """Regression tests for #5226: the ref-list title rendered as an h2
    inside the ul."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.transform = etree.XSLT(etree.parse(settings.BUILTIN_XSL_PATH))

    def render(self, title_block):
        jats = JATS_TEMPLATE.format(title=title_block)
        return self.transform(etree.fromstring(jats.encode("utf-8")))

    def test_ref_list_title_renders_before_list_not_inside_it(self):
        html = self.render("<title>Works Cited</title>")
        self.assertEqual(html.xpath('//div[@id="reflist"]//ul//h2'), [])
        heading = html.xpath('//h2[@id="reference-header"]')[0]
        self.assertEqual(heading.text, "Works Cited")
        self.assertEqual(heading.getnext(), html.xpath('//div[@id="reflist"]')[0])
        self.assertTrue(html.xpath('//div[@id="reflist"]/ul/li[@id="ref1"]'))

    def test_ref_list_without_title_gets_heading_outside_list(self):
        html = self.render("")
        self.assertEqual(html.xpath('//div[@id="reflist"]//ul//h2'), [])
        heading = html.xpath('//h2[@id="reference-header"]')[0]
        self.assertEqual(heading.text, "References")


TABLE_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<article xmlns:xlink="http://www.w3.org/1999/xlink" article-type="research-article">
  <body>
    <sec>
      <table-wrap{id}>
        <label>Table 1</label>
        <caption><p>Results</p></caption>
        <table><tr><td>1</td></tr></table>
      </table-wrap>
    </sec>
  </body>
</article>
"""


class TestTableLabelTransform(SimpleTestCase):
    """The "View Larger Table" button is described by "{table id}-label", so
    the label must carry that id."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.transform = etree.XSLT(etree.parse(settings.BUILTIN_XSL_PATH))

    def render(self, table_id):
        jats = TABLE_TEMPLATE.format(id=f' id="{table_id}"' if table_id else "")
        return self.transform(etree.fromstring(jats.encode("utf-8")))

    def test_table_label_id_follows_the_table_id(self):
        html = self.render("T1")
        self.assertTrue(html.xpath('//div[@class="table-expansion"][@id="T1"]'))
        self.assertEqual(
            html.xpath('//span[@class="table-label"]/@id'),
            ["T1-label"],
        )

    def test_table_without_an_id_keeps_a_numbered_label_id(self):
        html = self.render(None)
        self.assertEqual(
            html.xpath('//span[@class="table-label"]/@id'),
            ["tab1-label"],
        )
