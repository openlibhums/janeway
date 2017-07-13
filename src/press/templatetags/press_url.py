import mimetypes

from django import template
from django.utils.safestring import mark_safe

from press import models as press_models

register = template.Library()


@register.simple_tag
def press_url(request):
    return press_models.Press.get_press(request).press_url(request)


@register.simple_tag
def svg(filename):
    path = filename

    if not path:
        return None

    mimetype = mimetypes.guess_type(path, strict=True)
    if not mimetype or mimetype[0] != 'image/svg+xml':
        return None

    if isinstance(path, (list, tuple)):
        path = path[0]

    try:
        with open(path) as svg_file:
            return mark_safe(svg_file.read())
    except FileNotFoundError:
        return None
