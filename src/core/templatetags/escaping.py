import html

from django import template

register = template.Library()

@register.filter
def unescape(value):
    """ Unescapes all HTML tags and entities
    Can be used with `striptags` to ensure entities are turned into plain text
    e.g : {{ some_html | striptags | unescape}}
    """
    return html.unescape(value)
