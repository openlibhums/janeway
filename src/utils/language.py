__copyright__ = "Copyright 2025 Birkbeck, University of London"
__author__ = "Birkbeck Centre for Technology and Publishing"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


def find_language_or_its_variant(requested_language, available_languages):
    """
    Resolves a requested language against the languages a journal offers.

    Returns, in priority order:
    - the requested language, if it is available, or
    - the base language of the requested language (e.g. en for en-GB), or
    - a variant of the requested language (e.g. en-US for en-GB), or
    - None if no suitable language is available.

    When several variants match, the alphabetically-first is returned; the
    order of available_languages is not significant.
    """
    if not requested_language or not available_languages:
        return None

    if requested_language in available_languages:
        return requested_language

    base_language = requested_language.split("-")[0]

    if base_language in available_languages:
        return base_language

    base_matches = [
        lang for lang in available_languages if lang.startswith(base_language + "-")
    ]
    if base_matches:
        return sorted(base_matches)[0]

    return None


def register_missing_language_info():
    """
    Adds a Django LANG_INFO entry for each of settings.LANGUAGES that lacks one.

    Django's get_language_info falls back to the base language for a code it
    does not know, so en-us is reported with the code "en" and the language
    switchers list English twice (#5672). Existing entries are left alone.
    """
    from django.conf import settings
    from django.conf.locale import LANG_INFO

    for code, name in settings.LANGUAGES:
        code = code.lower()
        if code in LANG_INFO:
            continue
        LANG_INFO[code] = {
            "bidi": code.split("-")[0] in settings.LANGUAGES_BIDI,
            "code": code,
            "name": str(name),
            "name_local": str(name),
        }
