__copyright__ = "Copyright 2021 Birkbeck, University of London"
__author__ = "Martin Paul Eve, Mauro Sanchez & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.utils import translation
from django.conf import settings

from utils.logger import get_logger
from utils.middleware import BaseMiddleware

logger = get_logger(__name__)


class LanguageMiddleware(BaseMiddleware):
    @staticmethod
    def process_request(request):
        """
        Sets up language settings on the request for the translation override to use.
        The actual language constraint logic is handled by the translation override.
        """
        if request.journal:
            available_languages = request.journal.get_setting(
                group_name="general",
                setting_name="journal_languages",
            )
            default_language = request.journal.get_setting(
                group_name="general", setting_name="default_journal_language"
            )
            allow_language_switching = request.journal.get_setting(
                group_name="general", setting_name="switch_language"
            )

            request.available_languages = set(available_languages)
            request.default_language = default_language

            current_language = translation.get_language()
            translation.activate(current_language)
            request.current_language = current_language
