import mimetypes

from django import template
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.http import Http404

from press import models as press_models
register = template.Library()


@register.simple_tag
def press_url(request):
    return press_models.Press.get_press(request).press_url(request)


@register.simple_tag
def svg(filename):
    path = filename

    if not path:
        raise Http404

    mimetype = mimetypes.guess_type(path, strict=True)
    if not mimetype or mimetype[0] != 'image/svg+xml':
        return mark_safe('<img src="{url}">'.format(url=reverse('press_cover_download')))

    if isinstance(path, (list, tuple)):
        path = path[0]

    try:
        with open(path) as svg_file:
            return mark_safe(svg_file.read())
    except FileNotFoundError:
        raise Http404
