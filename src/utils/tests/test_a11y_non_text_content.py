__copyright__ = "Copyright 2026 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

"""WCAG 2.2 success criterion 1.1.1 Non-text Content.

Every place a Front of House theme outputs an image must let an editor
supply alt text. Static assets shipped with Janeway (icons, logos) may carry
fixed alt text, including alt="" when decorative. Images whose source comes
from the database (uploads, covers, profile pictures, press and journal
logos) must take their alt text from the AltText system, so it can be
edited in the back office.

The themes checked are the Front of House areas in a11y/conformance_data.json,
which feeds the update_a11y_conformance command that builds the VPAT.

Audit: https://github.com/openlibhums/janeway/issues/5568
"""

import json
import os
import re

from django.conf import settings
from django.test import SimpleTestCase

CONFORMANCE_DATA = os.path.join(settings.BASE_DIR, "a11y", "conformance_data.json")
THEMES_DIR = os.path.join(settings.BASE_DIR, "themes")
SHARED_TEMPLATES_DIR = os.path.join(settings.BASE_DIR, "templates", "common")

AREA_THEME_OVERRIDES = {
    "accessibility_mode": "clarity",
}
AREAS_WITHOUT_THEME = {"back_office"}

TEMPLATE_CODE = re.compile(r"\{%.*?%\}|\{\{.*?\}\}", re.S)
COMMENTS = re.compile(
    r"<!--.*?-->|\{#.*?#\}|\{%\s*comment\s*%\}.*?\{%\s*endcomment\s*%\}",
    re.S,
)
IMG_TAG = re.compile(r"<img\b[^>]*>", re.I)
ATTRIBUTE = re.compile(r"""([\w:-]+)\s*=\s*("[^"]*"|'[^']*')""")
PLACEHOLDER = re.compile(r"\x00(\d+)\x00")
STATIC_OR_CONTROL_TAG = re.compile(
    r"\{%\s*(static|if|elif|else|endif)\b.*?%\}",
    re.S,
)
ALT_TEXT_ASSIGNMENT = re.compile(r"\{%\s*get_alt_text\b[^%]*?\bas\s+(\w+)\s*%\}")
VARIABLE = re.compile(r"\{\{\s*([\w.]+)")
SVG_OR_IMAGE_TAG = re.compile(r"\{%\s*svg_or_image\b(.*?)%\}", re.S)
ALT_TEXT_ARGUMENT = re.compile(r"\balt_text=(\S+)")
INLINE_SVG_TAG = re.compile(r"\{%\s*svg\s+(\S+)(.*?)%\}", re.S)
QUOTED = re.compile(r"""\A(["']).*\1\Z""")
SVG_ELEMENT = re.compile(r"<svg\b[^>]*>", re.I)
SVG_TITLE = re.compile(r"\s*<title\b", re.I)


def theme_for_area(area_key):
    theme = AREA_THEME_OVERRIDES.get(area_key, area_key)
    for name in os.listdir(THEMES_DIR):
        if name.lower() == theme.lower():
            return name
    return None


def front_of_house_themes():
    with open(CONFORMANCE_DATA, encoding="utf-8") as f:
        areas = json.load(f)["area"]
    return {
        area_key: theme_for_area(area_key)
        for area_key in areas
        if area_key not in AREAS_WITHOUT_THEME
    }


def template_files(*directories):
    for directory in directories:
        for root, _, files in os.walk(directory):
            for name in sorted(files):
                if name.endswith(".html"):
                    yield os.path.join(root, name)


def mask_template_code(source):
    """Swap template tags for placeholders so HTML can be matched safely.

    Template tags inside attribute values often contain quotes and '>',
    which would otherwise end the attribute or the tag early.
    """
    blocks = []

    def stash(match):
        blocks.append(match.group(0))
        return f"\x00{len(blocks) - 1}\x00"

    return TEMPLATE_CODE.sub(stash, source), blocks


def unmask(value, blocks):
    return PLACEHOLDER.sub(lambda m: blocks[int(m.group(1))], value)


def is_dynamic_source(src):
    """True when the image comes from data rather than a shipped asset."""
    remainder = STATIC_OR_CONTROL_TAG.sub("", src)
    return "{{" in remainder or "{%" in remainder


def is_editable_alt(alt, alt_text_names):
    if "get_alt_text" in alt:
        return True
    for variable in VARIABLE.findall(alt):
        # A bare name must be assigned by get_alt_text in the template;
        # a property such as article.best_large_image_alt_text reads AltText.
        if variable in alt_text_names:
            return True
        if "." in variable and variable.split(".")[-1].endswith("alt_text"):
            return True
    return False


def image_problems(source):
    source = COMMENTS.sub(lambda m: "\n" * m.group(0).count("\n"), source)
    alt_text_names = set(ALT_TEXT_ASSIGNMENT.findall(source))
    masked, blocks = mask_template_code(source)

    for tag in IMG_TAG.finditer(masked):
        attributes = {
            name.lower(): unmask(value[1:-1], blocks)
            for name, value in ATTRIBUTE.findall(tag.group(0))
        }
        line = masked.count("\n", 0, tag.start()) + 1
        src = attributes.get("src") or attributes.get("data-src", "")

        if "alt" not in attributes:
            yield line, "no alt attribute"
        elif is_dynamic_source(src) and not is_editable_alt(
            attributes["alt"], alt_text_names
        ):
            yield line, "alt text on a data-driven image cannot be edited"

    # svg_or_image renders an <img> from an uploaded file, and svg renders a
    # file inline. Both take alt_text, used as the alt attribute or the SVG's
    # aria-label. A quoted path to svg is a shipped asset, which may have
    # fixed alt text.
    tags = [(tag, tag.group(1), False) for tag in SVG_OR_IMAGE_TAG.finditer(source)] + [
        (tag, tag.group(2), bool(QUOTED.match(tag.group(1))))
        for tag in INLINE_SVG_TAG.finditer(source)
    ]
    for tag, arguments, is_static in tags:
        line = source.count("\n", 0, tag.start()) + 1
        alt_text = ALT_TEXT_ARGUMENT.search(arguments)
        if not alt_text:
            yield line, "image tag without alt_text"
        elif not is_static and not is_editable_alt(
            f"{{{{ {alt_text.group(1)} }}}}", alt_text_names
        ):
            yield line, "alt text on a data-driven image cannot be edited"

    for tag in SVG_ELEMENT.finditer(masked):
        attributes = {
            name.lower(): value[1:-1] for name, value in ATTRIBUTE.findall(tag.group(0))
        }
        if attributes.get("aria-hidden") == "true":
            continue
        named = (
            "aria-label" in attributes
            or "aria-labelledby" in attributes
            or SVG_TITLE.match(masked, tag.end())
        )
        if attributes.get("role") != "img" or not named:
            line = masked.count("\n", 0, tag.start()) + 1
            yield line, "svg is neither hidden nor a named image"


def file_image_problems(path):
    with open(path, encoding="utf-8") as f:
        return list(image_problems(f.read()))


class ImageClassificationTests(SimpleTestCase):
    def assertAllowsAltText(self, template):
        self.assertEqual(list(image_problems(template)), [])

    def assertProblem(self, template, reason):
        self.assertEqual([r for _, r in image_problems(template)], [reason])

    def test_static_asset_with_fixed_alt_passes(self):
        self.assertAllowsAltText(
            """<img src="{% static 'common/img/icons/orcid.png' %}" alt="ORCID logo">"""
        )

    def test_decorative_static_asset_passes(self):
        self.assertAllowsAltText("""<img src="/static/common/img/spacer.png" alt="">""")

    def test_static_fallbacks_in_conditionals_count_as_static(self):
        self.assertAllowsAltText(
            '<img src="{% if dark %}{% static "a.png" %}{% else %}'
            '{% static "b.png" %}{% endif %}" alt="Logo">'
        )

    def test_missing_alt_fails(self):
        self.assertProblem(
            """<img src="{% static 'common/img/icons/users.png' %}">""",
            "no alt attribute",
        )

    def test_uploaded_image_with_get_alt_text_passes(self):
        self.assertAllowsAltText(
            '<img src="{{ issue.cover_image.url }}" '
            'alt="{% get_alt_text obj=issue default=issue.display_title %}">'
        )

    def test_uploaded_image_with_assigned_alt_text_passes(self):
        self.assertAllowsAltText(
            "{% get_alt_text obj=request.press.thumbnail_image as logo_alt %}"
            '<img src="{% url \'press_cover_download\' %}" alt="{{ logo_alt }}">'
        )

    def test_uploaded_image_with_alt_text_property_passes(self):
        self.assertAllowsAltText(
            '<img src="{{ article.best_large_image_url }}" '
            'alt="{{ article.best_large_image_alt_text }}">'
        )

    def test_uploaded_image_with_unassigned_alt_text_variable_fails(self):
        self.assertProblem(
            '<img src="{{ article.thumbnail_url }}" alt="{{ thumbnail_alt_text }}">',
            "alt text on a data-driven image cannot be edited",
        )

    def test_uploaded_image_with_derived_alt_fails(self):
        self.assertProblem(
            '<img src="{{ issue.cover_image.url }}" alt="{{ issue.display_title }}">',
            "alt text on a data-driven image cannot be edited",
        )

    def test_quotes_and_brackets_inside_template_tags_parse(self):
        self.assertProblem(
            '<img src="{{ journal.default_cover_image.url }}" '
            'alt="{% if journal.name != "" and x > 1 %}{{ journal.name }}{% endif %}">',
            "alt text on a data-driven image cannot be edited",
        )

    def test_commented_out_images_are_ignored(self):
        self.assertAllowsAltText(
            '<!-- <img src="{{ x.url }}"> -->{# <img src="{{ y.url }}"> #}'
        )

    def test_svg_or_image_with_assigned_alt_text_passes(self):
        self.assertAllowsAltText(
            "{% get_alt_text file_path=request.journal.header_image as header_alt %}"
            "{% svg_or_image request.journal.header_image alt_text=header_alt %}"
        )

    def test_svg_or_image_without_alt_text_fails(self):
        self.assertProblem(
            "{% svg_or_image request.repository.logo %}",
            "image tag without alt_text",
        )

    def test_svg_or_image_with_derived_alt_text_fails(self):
        self.assertProblem(
            "{% svg_or_image request.repository.logo alt_text=request.repository.name %}",
            "alt text on a data-driven image cannot be edited",
        )

    def test_inline_svg_with_assigned_alt_text_passes(self):
        self.assertAllowsAltText(
            "{% get_alt_text obj=request.press.thumbnail_image as logo_alt %}"
            "{% svg request.press_cover alt_text=logo_alt %}"
        )

    def test_inline_svg_without_alt_text_fails(self):
        self.assertProblem(
            "{% svg request.press_cover %}",
            "image tag without alt_text",
        )

    def test_inline_svg_with_derived_alt_text_fails(self):
        self.assertProblem(
            "{% svg request.press_cover alt_text=request.press.name %}",
            "alt text on a data-driven image cannot be edited",
        )

    def test_shipped_inline_svg_with_fixed_alt_text_passes(self):
        self.assertAllowsAltText(
            '{% svg "static/common/img/sample/janeway.svg" alt_text="Janeway" %}'
        )

    def test_hidden_svg_element_passes(self):
        self.assertAllowsAltText(
            '<svg class="icon" aria-hidden="true" focusable="false"><path/></svg>'
        )

    def test_named_svg_element_passes(self):
        self.assertAllowsAltText('<svg role="img"><title>Logo</title><path/></svg>')
        self.assertAllowsAltText('<svg role="img" aria-label="Logo"><path/></svg>')

    def test_unhidden_svg_element_fails(self):
        self.assertProblem(
            '<svg class="icon" viewBox="0 0 24 24"><path/></svg>',
            "svg is neither hidden nor a named image",
        )


class NonTextContentTests(SimpleTestCase):
    def test_conformance_areas_map_to_themes(self):
        for area_key, theme in front_of_house_themes().items():
            with self.subTest(area=area_key):
                self.assertIsNotNone(
                    theme,
                    f"Area '{area_key}' in conformance_data.json has no matching "
                    f"theme in {THEMES_DIR}. Add it to AREA_THEME_OVERRIDES "
                    f"or AREAS_WITHOUT_THEME.",
                )

    def test_every_image_allows_alt_text(self):
        for area_key, theme in front_of_house_themes().items():
            if theme is None:
                continue
            theme_templates = os.path.join(THEMES_DIR, theme, "templates")
            problems = [
                f"{os.path.relpath(path, settings.BASE_DIR)}:{line} {reason}"
                for path in template_files(theme_templates, SHARED_TEMPLATES_DIR)
                for line, reason in file_image_problems(path)
            ]
            with self.subTest(area=area_key, theme=theme):
                if problems:
                    self.fail(
                        f"{len(problems)} image(s) in the {theme} theme do not "
                        f"allow alt text (WCAG 1.1.1):\n" + "\n".join(problems)
                    )
