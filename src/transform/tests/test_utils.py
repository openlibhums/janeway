from django.test import SimpleTestCase

from transform.utils import convert_html_abstract_to_jats


class TestConvertHtmlAbstractToJats(SimpleTestCase):
    """Regression tests for convert_html_abstract_to_jats.

    The function must handle HTML entities (e.g. &nbsp;, &mdash;) that are
    valid HTML but not valid XML — previously these caused silent empty output
    in Crossref deposits (issue #5262).
    """

    def test_empty_inputs(self):
        self.assertEqual(convert_html_abstract_to_jats(""), "")
        self.assertEqual(convert_html_abstract_to_jats(None), "")

    def test_basic_formatting(self):
        result = convert_html_abstract_to_jats(
            "<p>Plain text.</p><p><strong>Bold</strong> and <em>italic</em>.</p>"
        )
        self.assertIn("Plain text.", result)
        self.assertIn("<bold>Bold</bold>", result)
        self.assertIn("<italic>italic</italic>", result)

    def test_html_entities_do_not_produce_empty_output(self):
        # &nbsp;, &mdash;, &ldquo;/&rdquo; are valid HTML but not XML —
        # they must not cause the function to silently return ""
        for entity, label in [
            ("&nbsp;", "nbsp"),
            ("&mdash;", "mdash"),
            ("&ldquo;text&rdquo;", "curly quotes"),
        ]:
            with self.subTest(entity=label):
                result = convert_html_abstract_to_jats(f"<p>Test {entity} here.</p>")
                self.assertNotEqual(result, "", msg=f"{label} caused empty output")

    def test_nbsp_after_bold_label(self):
        # Common WYSIWYG pattern: <strong>Label:</strong>&nbsp;text
        result = convert_html_abstract_to_jats(
            "<p><strong>Results:</strong>&nbsp;212 patients.</p>"
        )
        self.assertNotEqual(result, "")
        self.assertIn("<bold>Results:</bold>", result)
        self.assertIn("212 patients.", result)

    def test_lt_entity_preserved(self):
        # &lt; is valid in both HTML and XML and must round-trip correctly
        result = convert_html_abstract_to_jats("<p>p&lt;0.00001</p>")
        self.assertNotEqual(result, "")
        self.assertIn("p&lt;0.00001", result)

    def test_multi_para_with_entities(self):
        # Reproduces the real-world abstract that triggered issue #5262
        abstract = (
            "<p><strong>Results:</strong>&nbsp;212 patients. p&lt;0.00001.</p>"
            "<p><strong>Conclusion:</strong>&nbsp;Reliable in stages 1&mdash;3.</p>"
        )
        result = convert_html_abstract_to_jats(abstract)
        self.assertNotEqual(result, "")
        self.assertIn("212 patients.", result)
        self.assertIn("<bold>Conclusion:</bold>", result)
