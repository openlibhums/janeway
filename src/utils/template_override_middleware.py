__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import errno
import io
import os
import warnings

from django.conf import settings
from django.template.loaders.filesystem import Loader as FileSystemLoader

from utils import setting_handler, function_cache, logic as utils_logic


class Loader(FileSystemLoader):

    @staticmethod
    @function_cache.cache(120)
    def journal_theme(journal):
        return setting_handler.get_setting('general', 'journal_theme', journal).value

    @staticmethod
    @function_cache.cache(120)
    def base_theme(journal):
        return setting_handler.get_setting('general', 'journal_base_theme', journal).value

    def get_theme_dirs(self):
        from core import models as core_models
        request = utils_logic.get_current_request()
        base_theme, theme_setting = None, None

        if request:
            if request.journal:
                # this is a journal, and we should attempt to retrieve any theme settings
                try:
                    theme_setting = self.journal_theme(request.journal)
                except core_models.Setting.DoesNotExist:
                    pass

                try:
                    base_theme = self.base_theme(request.journal)
                except core_models.Setting.DoesNotExist:
                    pass

            elif request.repository:
                theme_setting = 'OLH'
                if (
                        request.repository.theme and
                        request.repository.theme in settings.REPOSITORY_THEMES
                ):
                    theme_setting = request.repository.theme
            else:
                # this is the press site
                theme_setting = request.press.theme

        # allows servers in debug mode to override the theme with ?theme=name in the URL
        if settings.DEBUG and request and request.GET.get('theme'):
            theme_setting = request.GET.get('theme')

        # order up the themes and return them with engine dirs
        themes_in_order = list()

        if theme_setting:
            themes_in_order.append(
                os.path.join(settings.BASE_DIR, 'themes', theme_setting, 'templates')
            )
        if base_theme:
            themes_in_order.append(
                os.path.join(settings.BASE_DIR, 'themes', base_theme, 'templates')
            )

        # if the base_theme and INSTALLATION_BASE_THEME are different,
        # append the INSTALLATION_BASE_THEME.
        if not base_theme == settings.INSTALLATION_BASE_THEME:
            themes_in_order.append(
                os.path.join(settings.BASE_DIR, 'themes', settings.INSTALLATION_BASE_THEME, 'templates')
            )

        return themes_in_order + self.engine.dirs

    def get_dirs(self):
        return self.get_theme_dirs()
