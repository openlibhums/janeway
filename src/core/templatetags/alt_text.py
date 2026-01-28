import hashlib

from django import template
from django.template.defaultfilters import slugify
from django.template.loader import render_to_string

from core import models

register = template.Library()


@register.filter
def encode_file_path(value):
    """
    Encode a file path string to an MD5 hash.

    :param value: File path string to encode
    :return: MD5 hexadecimal hash of the value, or empty string if value is falsy
    """
    if not value:
        return ""
    return hashlib.md5(value.encode()).hexdigest()


@register.simple_tag
def get_alt_text(obj=None, file_path=None, token=None, default=""):
    """
    Render alt text for a file given a context phrase.
    Priority order for identifier: file_path > token > None.
    file_path will be hashed using MD5 before lookup.

    :param obj: Model instance to associate with the alt text
    :param file_path: File path string to hash and use as identifier
    :param token: Pre-computed token/hash to use as identifier
    :param default: Default text to return if no alt text is found
    :return: The alt text string, default value if alt text is empty, or empty string
    """
    if file_path:
        path = encode_file_path(file_path.strip())
    elif token:
        path = token
    else:
        path = None

    alt_text = models.AltText.get_text(
        obj=obj,
        path=path,
    )

    if alt_text == "" and default:
        return default

    return str(alt_text)


@register.simple_tag
def get_admin_alt_text_snippet(obj=None, file_path=None, token=None):
    """
    Render a block of alt text wrapped in HTML for admin interface with HTMX targeting.
    Priority order for identifier: file_path > token > None.
    file_path will be hashed using MD5 before lookup.

    :param obj: Model instance to associate with the alt text
    :param file_path: File path string to hash and use as identifier
    :param token: Pre-computed token/hash to use as identifier
    :return: Rendered HTML string from the alt_text_snippet.html template
    """
    if file_path:
        path = encode_file_path(file_path.strip())
    elif token:
        path = token
    else:
        path = None

    alt_text = models.AltText.get_text(
        obj=obj,
        path=path,
    )

    return render_to_string(
        "core/partials/alt_text/alt_text_snippet.html",
        {
            "alt_text": alt_text,
            "object": obj,
            "file_path": file_path,
            "token": token,
        },
    )


@register.filter
def model_string(obj):
    """
    Return the 'app_label.modelname' string for a Django model instance.

    :param obj: Model instance
    :return: String in format 'app_label.modelname' or empty string if obj has no _meta
    """
    if hasattr(obj, "_meta"):
        return f"{obj._meta.app_label}.{obj._meta.model_name}"
    return ""


@register.filter
def app_label(obj):
    """
    Returns the app_label for a Django model instance.

    :param obj: Model instance
    :return: The app_label string or empty string if obj has no _meta attribute
    """
    try:
        return obj._meta.app_label
    except AttributeError:
        return ""


@register.simple_tag
def get_id_token(obj=None, file_path=None, token=None):
    """
    Returns a slugified identifier string based on a model instance, token, or file path.
    Priority order: obj > token > file_path > fallback.

    :param obj: Model instance to generate ID from
    :param file_path: File path string to hash and use as identifier
    :param token: Pre-existing token/hash to use as identifier
    :return: Slugified identifier string or 'unknown-id-token' if no arguments provided
    """
    if obj:
        return slugify(f"{model_string(obj)}-{obj.pk}")
    elif token:
        return token
    elif file_path:
        return encode_file_path(file_path)
    return "unknown-id-token"
