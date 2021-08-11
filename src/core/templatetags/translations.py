from django import template
from django.conf.locale import LANG_INFO

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
        return info.get('name_local')
    except (KeyError, AttributeError):
        return language_code
