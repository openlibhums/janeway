__copyright__ = "Copyright 2021 Birkbeck, University of London"
__author__ = "Martin Paul Eve, Mauro Sanchez & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.conf import settings
from django.middleware.locale import LocaleMiddleware
from django.utils import translation

from utils.language import find_language_or_its_variant
from utils.logger import get_logger

logger = get_logger(__name__)


class JournalLocaleMiddleware(LocaleMiddleware):
    """
    A LocaleMiddleware that constrains the active language to those a journal
    publishes in.

    Django's LocaleMiddleware selects a language from the session, the language
    cookie or the Accept-Language header. On a journal site we additionally
    require that language to be one the journal offers; otherwise the journal's
    ``default_journal_language`` is used. This stops, for instance, a
    Spanish-only journal being rendered with an English navigation bar simply
    because the visitor's browser was last used on an English site (see #4313).

    Response handling (Content-Language and Vary headers) is inherited from
    Django's LocaleMiddleware unchanged.
    """

    def process_request(self, request):
        journal = getattr(request, "journal", None)

        if not journal or not settings.USE_I18N:
            return super().process_request(request)

        available_languages = list(
            journal.get_setting(
                group_name="general",
                setting_name="journal_languages",
            )
            or []
        )
        default_language = (
            journal.get_setting(
                group_name="general",
                setting_name="default_journal_language",
            )
            or settings.LANGUAGE_CODE
        )

        # The default language must always be selectable.
        if default_language not in available_languages:
            available_languages.append(default_language)

        requested_language = translation.get_language_from_request(
            request,
            check_path=False,
        )
        language = find_language_or_its_variant(
            requested_language,
            available_languages,
        )
        if not language:
            logger.debug(
                "Requested language %s is not offered by the journal; "
                "falling back to the default: %s",
                requested_language,
                default_language,
            )
            language = default_language

        translation.activate(language)
        request.LANGUAGE_CODE = translation.get_language()
        request.available_languages = set(available_languages)
        request.default_language = default_language
        request.current_language = request.LANGUAGE_CODE
