import functools

from django import template
from django.conf.locale import LANG_INFO
from django.contrib.staticfiles import finders
from django.templatetags.static import static

register = template.Library()


@register.filter
def language_name(language_code):
    """
    Takes a language code eg en and returns its name from settings.

    {% load translations %}

    {{ string|language_name }}
    """
    try:
        info = LANG_INFO.get(language_code)
        return info.get("name_local")
    except (KeyError, AttributeError):
        return language_code


@functools.lru_cache(maxsize=None)
def _language_flag(language_code):
    path = "common/img/flags/{}.png".format(language_code)
    if finders.find(path):
        return static(path)
    return ""


@register.filter
def language_flag(language_code):
    """
    Returns the URL of the flag image for a language code, or an empty string
    when Janeway has no flag for it, so a theme can fall back to text.

    {% load translations %}

    {{ language.code|language_flag }}
    """
    return _language_flag(language_code)
