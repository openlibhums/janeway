from django.utils import translation
from django.conf import settings
from utils.logger import get_logger
from core.middleware import _threadlocal

logger = get_logger(__name__)

_original_get_language = translation.get_language


def find_language_or_its_variant(requested_language, available_languages):
    """
    This function checks language avaliability and returns (in priority order):
    - the requested language, or
    - the base language of the requested language, or
    - a variant of the requested language, or
    - None.
    """
    if not requested_language or not available_languages:
        return None

    if requested_language in available_languages:
        return requested_language

    base_language = requested_language.split("-")[0]
    base_matches = [
        lang for lang in available_languages if lang.startswith(base_language + "-")
    ]

    if base_language in available_languages:
        return base_language

    if base_matches:
        return base_matches[0]

    return None


def get_constrained_language():
    """
    Constrains the language to the closest available language for the current journal.
    Caches it on the request object.
    """
    request = getattr(_threadlocal, "request", None)

    if not request or not hasattr(request, "journal") or not request.journal:
        return _original_get_language()

    # Handle Single Language only journals
    # Use the stored value from middleware instead of calling get_setting()
    switch_language_enabled = getattr(request, "allow_language_switching", True)
    try:
        switch_language_enabled = request.journal.get_setting(
            group_name="general", setting_name="switch_language"
        )
    finally:
        # Restore our overridden function
        translation.get_language = original_get_language

    if (
        hasattr(request, "_single_language")
        or not settings.USE_I18N
        or not switch_language_enabled
    ):
        default_language = getattr(request, "default_language", None)
        request._single_language = default_language or settings.LANGUAGE_CODE
        return request._single_language

    # Constrain language to those avaliable
    if hasattr(request, "_constrained_language") and hasattr(
        request, "_constrained_input_language"
    ):
        cached_language = request._constrained_language
        current_language = _original_get_language()
        if current_language == request._constrained_input_language:
            return cached_language

    # Get current language from request.LANGUAGE_CODE to avoid recursion
    current_language = getattr(request, "LANGUAGE_CODE", None)
    if not current_language:
        current_language = _original_get_language()

    available_languages = getattr(request, "available_languages", None)

    constrained_language = find_language_or_its_variant(
        current_language, available_languages
    )
    if not constrained_language:
        default_language = getattr(request, "default_language", None)
        if not default_language:
            default_language = settings.LANGUAGE_CODE
        constrained_language = default_language

    request._constrained_language = constrained_language
    request._constrained_input_language = current_language

    return constrained_language
