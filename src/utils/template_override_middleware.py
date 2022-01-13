__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import errno
import io
import os
import threading
import warnings

from django.conf import settings
from django.core.exceptions import SuspiciousFileOperation
from django.template import Origin, TemplateDoesNotExist
from django.template.loaders.base import Loader as BaseLoader
from django.utils._os import safe_join
from django.utils.deprecation import RemovedInDjango20Warning

from utils import setting_handler, function_cache

_local = threading.local()


class ThemeEngineMiddleware(object):
    """ Handles theming through middleware
    """

    def process_request(self, request):
        _local.request = request

    def process_response(self, request, response):
        if hasattr(_local, 'request'):
            del _local.request
        return response


class Loader(BaseLoader):

    @function_cache.cache(120)
    def query_theme_dirs(self, journal):
        return setting_handler.get_setting('general', 'journal_theme', journal).value

    def get_theme_dirs(self):

        if hasattr(_local, 'request'):

            if _local.request.journal:
                # this is a journal and we should attempt to retrieve any theme settings
                try:
                    theme_setting = self.query_theme_dirs(_local.request.journal)
                except Exception:
                    theme_setting = 'clean'

            elif _local.request.repository:
                theme_setting = 'material'
            else:
                # this is the press site
                theme_setting = _local.request.press.theme
        else:
            # for some reason the request has not been pulled into the local thread.
            # we shouldn't really ever arrive here during a request that requires a template
            theme_setting = 'clean'

        # this is a backup for a missed setting get above.
        if not theme_setting:
            theme_setting = 'clean'

        if settings.DEBUG and hasattr(_local, 'request') and _local.request.GET.get('theme'):
            theme_setting = _local.request.GET.get('theme')

        return [os.path.join(settings.BASE_DIR, 'themes', theme_setting, 'templates'),
                os.path.join(settings.BASE_DIR, 'themes', 'clean', 'templates')] + self.engine.dirs

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
