__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import errno
import io
import os
import warnings

from django.conf import settings
from django.core.exceptions import SuspiciousFileOperation
from django.template import Origin, TemplateDoesNotExist
from django.template.loaders.base import Loader as BaseLoader
from django.utils._os import safe_join
from django.utils.deprecation import RemovedInDjango20Warning

from utils import setting_handler, function_cache, logic as utils_logic


class Loader(BaseLoader):

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
                # this is a journal and we should attempt to retrieve any theme settings
                try:
                    theme_setting = self.journal_theme(request.journal)
                except core_models.Setting.DoesNotExist:
                    pass

                try:
                    base_theme = self.base_theme(request.journal)
                except core_models.Setting.DoesNotExist:
                    pass

            elif request.repository:
                # only the material theme supports repositories at the moment.
                theme_setting = 'material'
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

    def get_contents(self, origin):
        try:
            with io.open(origin.name, encoding=self.engine.file_charset) as fp:
                return fp.read()
        except IOError as e:
            if e.errno == errno.ENOENT:
                raise TemplateDoesNotExist(origin)
            raise

    def get_template_sources(self, template_name, template_dirs=None):
        """
        Return an Origin object pointing to an absolute path in each directory
        in template_dirs. For security reasons, if a path doesn't lie inside
        one of the template_dirs it is excluded from the result set.
        """
        if not template_dirs:
            template_dirs = self.get_dirs()
        for template_dir in template_dirs:
            try:
                name = safe_join(template_dir, template_name)
            except SuspiciousFileOperation:
                # The joined path was located outside of this template_dir
                # (it might be inside another one, so this isn't fatal).
                continue

            yield Origin(
                name=name,
                template_name=template_name,
                loader=self,
            )

    def load_template_source(self, template_name, template_dirs=None):
        warnings.warn(
            'The load_template_sources() method is deprecated. Use '
            'get_template() or get_contents() instead.',
            RemovedInDjango20Warning,
        )
        for origin in self.get_template_sources(template_name, template_dirs):
            try:
                return self.get_contents(origin), origin.name
            except TemplateDoesNotExist:
                pass
        raise TemplateDoesNotExist(template_name)
