import mimetypes
import os

from django import template
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.conf import settings

from press import models as press_models
from utils.logger import get_logger

logger = get_logger(__name__)

register = template.Library()


@register.simple_tag
def press_url(request):
    return press_models.Press.get_press(request).site_url()


@register.simple_tag
def svg(filename):
    path = filename

    if not path:
        return None

    mimetype = mimetypes.guess_type(path, strict=True)

    if not mimetype or mimetype[0] != 'image/svg+xml':
        return mark_safe(
            '<img src="{url}" class="top-bar-image img-fluid">'.format(
                url=reverse('press_cover_download'),
            )
        )

    if isinstance(path, (list, tuple)):
        path = path[0]

    if not path.startswith(settings.BASE_DIR):
        path = os.path.join(settings.BASE_DIR, path)

    try:
        with open(path) as svg_file:
            return mark_safe(svg_file.read())
    except FileNotFoundError:
        return None


@register.simple_tag
def svg_or_image(image_field, css_class="", alt_text="", inline=False):
    """Renders the given image or SVG from a Field as DOM object
    :param image_field: An instance of core.model_utils.SVGImageField
    :param css_class: String to be added as the class attribute in the dom
    :param inline: Bool to control if the SVG is rendered as an <img>
        or inline. When rendering inline, the svg is served from the app and
        thus won't be cached by the browser. When rendering as an <img>
    :return: A DOM object of the image
    """
    if not image_field:
        return None

    mimetype = mimetypes.guess_type(image_field.path, strict=True)

    if not inline or not mimetype or mimetype[0] != 'image/svg+xml':
        return mark_safe(
            '<img src="{url}" class="{css_class} alt="{alt_text}">'.format(
                url=image_field.url,
                css_class=css_class,
                alt_text=alt_text,
            )
        )

    try:
        with open(image_field.path) as svg_file:
            return mark_safe(svg_file.read())
    except FileNotFoundError:
        logger.warning("Could not read SVG file %s", image_field.path)
        return None

