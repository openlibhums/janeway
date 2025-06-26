from django import template

from core.files import file_path_mime

register = template.Library()


@register.filter
def get_mime(file_field):
    """
    Template tag to retrieve the MIME type of an ImageField or FileField.
    If the field has no path attribute application/octet-stream is returned
    as the default.

    Usage: {{ request.press.favicon|get_mime }}
    """
    try:
        if file_field and hasattr(file_field, 'path'):
            return file_path_mime(file_field.path)
    except FileNotFoundError:
        pass
    return 'application/octet-stream'
