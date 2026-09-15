from django.test import SimpleTestCase

from core.widgets import OptGroupSelect
from utils.testing.helpers import render_widget


class TestOptGroupSelect(SimpleTestCase):
    def test_options_split_into_named_optgroups(self):
        html = render_widget(
            OptGroupSelect(groups={"Group A": {1}, "Group B": {2, 3}}),
            choices=[("", "---------"), (1, "Alice"), (2, "Bob"), (3, "Carol")],
        )
        self.assertIn('<optgroup label="Group A">', html)
        self.assertIn('<optgroup label="Group B">', html)
        self.assertIn("Alice", html)
        self.assertIn("Bob", html)
        self.assertIn("Carol", html)

    def test_empty_option_rendered_outside_optgroups(self):
        html = render_widget(
            OptGroupSelect(groups={"Editors": {1}}),
            choices=[("", "---------"), (1, "Alice")],
        )
        self.assertLess(html.index("---------"), html.index("<optgroup"))
