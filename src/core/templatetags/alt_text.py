import hashlib

from django import template
from django.template.defaultfilters import slugify
from django.template.loader import render_to_string

from core import models

register = template.Library()


@register.simple_tag
def get_alt_text(obj=None, file_path=None, token=None, context_phrase=None):
    """
    Render a block of alt text wrapped in a span with a unique ID for HTMX targeting.
    """
    if file_path:
        path = hashlib.sha256(file_path.strip().encode()).hexdigest()
    elif token:
        path = token
    else:
        path = None

    alt_text = models.AltText.get_text(
        obj=obj,
        path=path,
        context_phrase=context_phrase,
    )
    print(alt_text)
    return str(alt_text)


@register.simple_tag
def get_admin_alt_text_snippet(obj=None, file_path=None, token=None, context_phrase=None):
    """
    Render a block of alt text wrapped in a span with a unique ID for HTMX targeting.
    """
    if file_path:
        path = hashlib.sha256(file_path.strip().encode()).hexdigest()
    elif token:
        path = token
    else:
        path = None

    alt_text = models.AltText.get_text(
        obj=obj,
        path=path,
        context_phrase=context_phrase,
    )

    return render_to_string(
        "core/partials/alt_text/alt_text_snippet.html",
        {
            "alt_text": alt_text,
            "object": obj,
            "file_path": file_path,
            "token": token,
            "context_phrase": context_phrase,
        },
    )
@register.filter
def model_string(obj):
    """
    Return the 'app_label.modelname' string for a Django model instance.
    """
    if hasattr(obj, '_meta'):
        return f"{obj._meta.app_label}.{obj._meta.model_name}"
    return ''


@register.filter
def app_label(obj):
    """
    Returns 'app_label' for a model instance.
    """
    try:
        return obj._meta.app_label
    except AttributeError:
        return ''


@register.simple_tag
def get_id_token(obj=None, file_path=None, token=None):
    """
    Returns a slugified identifier string based on a model instance or file path.
    Priority: object > file_path
    """
    if obj:
        return slugify(model_string(obj))
    elif token:
        return token
    elif file_path:
        return hashlib.sha256(file_path.encode()).hexdigest()
    return "unknown-id-token"


@register.filter
def encode_file_path(value):
    if not value:
        return ''
    return hashlib.sha256(value.encode()).hexdigest()