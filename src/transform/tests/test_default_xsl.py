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
