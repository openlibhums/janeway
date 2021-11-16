__copyright__ = "Copyright 2021 Birkbeck, University of London"
__author__ = "Martin Paul Eve, Mauro Sanchez & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.utils import translation
from django.conf import settings

from utils.logger import get_logger

logger = get_logger(__name__)


class LanguageMiddleware(object):
    @staticmethod
    def process_request(request):
        """
        Checks that the currently set language is okay for the current journal.
        """
        if request.journal and settings.USE_I18N:
            current_language = translation.get_language()
            available_languages = request.journal.get_setting(
                group_name='general',
                setting_name='journal_languages',
            )
            default_language = request.journal.get_setting(
                group_name='general',
                setting_name='default_journal_language'
            )
            if current_language not in available_languages:
                translation.activate(settings.LANGUAGE_CODE)
                logger.debug('Current Language not in the available languages. Activating {}'.format(
                    settings.LANGUAGE_CODE,
                ))

            if not available_languages:
                # If we have no languages use the defaults from settings.
                available_languages = [lang[0] for lang in settings.LANGUAGES]
            else:
                # The default language must always be in available_languages.
                available_languages.append(settings.LANGUAGE_CODE)

            request.available_languages = set(available_languages)
            request.default_language = default_language
            request.current_language = translation.get_language()
