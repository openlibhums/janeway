import mimetypes
import os
import re
from functools import lru_cache

from django import template
from django.conf import settings
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from press import models as press_models
from utils.logger import get_logger

logger = get_logger(__name__)

register = template.Library()

# The root element, after any XML declaration, doctype or comments.
SVG_ROOT = re.compile(
    r"\A(?:\s|<\?.*?\?>|<!--.*?-->|<!DOCTYPE[^>]*>)*<svg\b",
    re.S | re.I,
)


@register.simple_tag
def press_url(request):
    return press_models.Press.get_press(request).site_url()


@lru_cache(maxsize=128)
def _labelled_svg(path, modified, alt_text):
    """Reads an SVG file and names its root element with alt_text.

    Cached per process. Including the file's modification time in the key
    means a replaced file is read again.
    """
    with open(path) as svg_file:
        markup = svg_file.read()
    if not alt_text:
        return markup
    root = SVG_ROOT.match(markup)
    if not root:
        return markup
    # The attributes go first, so they win over any the file already sets:
    # HTML parsers keep the first of a repeated attribute.
    return (
        markup[: root.end()]
        + format_html(' role="img" aria-label="{}"', alt_text)
        + markup[root.end() :]
    )


def inline_svg(path, alt_text=""):
    try:
        modified = os.stat(path).st_mtime_ns
        return mark_safe(_labelled_svg(path, modified, str(alt_text)))
    except FileNotFoundError:
        logger.warning("Could not read SVG file %s", path)
        return None


@register.simple_tag
def svg(filename, alt_text=""):
    """Renders an SVG file inline, or an <img> for any other file type
    :param filename: Path to the file, absolute or relative to BASE_DIR
    :param alt_text: Text alternative, set as the SVG's aria-label or the
        <img> alt attribute
    """
    path = filename

    if not path:
        return None

    mimetype = mimetypes.guess_type(path, strict=True)

    if not mimetype or mimetype[0] != "image/svg+xml":
        return format_html(
            '<img src="{}" class="top-bar-image img-fluid" alt="{}">',
            reverse("press_cover_download"),
            alt_text,
        )

    if isinstance(path, (list, tuple)):
        path = path[0]

    if not path.startswith(settings.BASE_DIR):
        path = os.path.join(settings.BASE_DIR, path)

    return inline_svg(path, alt_text)


@register.simple_tag
def svg_or_image(image_field, css_class="", alt_text="", inline=False):
    """Renders the given image or SVG from a Field as DOM object
    :param image_field: An instance of core.model_utils.SVGImageField
    :param css_class: String to be added as the class attribute in the dom
    :param alt_text: Text alternative, set as the <img> alt attribute or
        the inline SVG's aria-label
    :param inline: Bool to control if the SVG is rendered as an <img>
        or inline. When rendering inline, the svg is served from the app and
        thus won't be cached by the browser. When rendering as an <img>
    :return: A DOM object of the image
    """
    if not image_field:
        return None

    mimetype = mimetypes.guess_type(image_field.path, strict=True)

    if not inline or not mimetype or mimetype[0] != "image/svg+xml":
        return format_html(
            '<img src="{}" class="{}" alt="{}">',
            image_field.url,
            css_class,
            alt_text,
        )

    return inline_svg(image_field.path, alt_text)
