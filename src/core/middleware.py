__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import logging
from uuid import uuid4
import _thread as thread

from django.contrib.sites import models as site_models
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.http import Http404
from django.core.exceptions import PermissionDenied
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import redirect
from django.conf import settings

from press import models as press_models
from utils import models as util_models, setting_handler
from core import models as core_models
from journal import models as journal_models


def get_site_resources(request):
    """ Attempts to match the relevant resources for the request url

    Result depends on the value of settings.URL_CONFIG
    :param request: A Django HttpRequest
    :return: press.models.Press,journal.models.Journal,HttpResponseRedirect
    """
    journal = press = redirect_obj = None
    try: #try journal site
        if settings.URL_CONFIG == 'path':
            code = request.path.split('/')[1]
            journal = journal_models.Journal.objects.get(code=code)
            press = journal.press
        elif settings.URL_CONFIG == 'domain':
            journal = journal_models.Journal.get_by_request(request)
            press = journal.press
        else:
            raise ImproperlyConfigured(
                    "'%s' is not a valid value for settings.URL_CONFIG"
                    "" % settings.URL_CONFIG
            )
    except (journal_models.Journal.DoesNotExist, IndexError):
        try: #try press site
            press = press_models.Press.get_by_request(request)
        except press_models.Press.DoesNotExist:
            try: #try press site
                alias = core_models.DomainAlias.get_by_request(request)
                if alias.redirect:
                    redirect_obj = redirect(alias.build_redirect_url(request))
                else:
                    journal = alias.journal
                    press = journal.press
            except core_models.DomainAlias.DoesNotExist:
                #Give up
                logging.warning(
                    "Couldn't match a resource for %s, redirecting to %s"
                    "" % (request.path, settings.DEFAULT_HOST)
                )
                redirect_obj = redirect(settings.DEFAULT_HOST)

    return journal, press, redirect_obj


class SiteSettingsMiddleware(object):
    @staticmethod
    def process_request(request):
        """ This middleware class sets a series of variables for templates and views to access inside the request object

        :param request: the current request
        :return: None or an http 404 error in the event of catastrophic failure
        """

        # Attempt to get the current site. If it isn't found, check for an alias object and use that site.
        journal, press, redirect_obj = get_site_resources(request)
        logging.warning(journal)
        if redirect_obj is not None:
            return redirect_obj

        request.port = request.META['SERVER_PORT']
        request.press = press
        request.press_cover = press.press_cover(request)
        request.press_base_url = press.press_url(request)

        if journal is not None:
            request.journal = journal
            request.journal_base_url = journal.full_url(request)
            request.journal_cover = journal.override_cover(request)
            request.site_type = journal
            request.model_content_type = ContentType.objects.get_for_model(
                    journal)

        elif press is not None:
            request.journal = None
            request.site_type = press
            request.model_content_type = ContentType.objects.get_for_model(press)
        else:
            raise Http404()
        # We check if the journal and press are set to be secure and redirect if the current request is not secure.
        if not request.is_secure():
            if request.journal and request.journal.get_setting('general', 'is_secure') and not request.is_secure() \
                    and not settings.DEBUG:
                return redirect("https://{0}{1}".format(request.get_host(), request.path))
            elif not request.journal and request.press.is_secure and not request.is_secure() and not settings.DEBUG:
                return redirect("https://{0}{1}".format(request.get_host(), request.path))

    def process_view(self, request, view_func, view_args, view_kwargs):
        if settings.URL_CONFIG == 'path':
            try:
                view_kwargs.pop('journal_code')
            except KeyError:
                pass


class MaintenanceModeMiddleware(object):
    @staticmethod
    def process_request(request):
        if request.journal is not None:
            maintenance_mode_setting = setting_handler.get_setting('general', 'maintenance_mode', request.journal)
            if maintenance_mode_setting and maintenance_mode_setting.processed_value:

                if hasattr(request, 'user') and request.user.is_staff:
                    return None

                if request.path == '/login/':
                    return None

                maintenance_mode_message = setting_handler.get_setting('general', 'maintenance_message',
                                                                       request.journal)
                request.META['maintenance_mode'] = maintenance_mode_message
                raise PermissionDenied(request, maintenance_mode_message)


class CounterCookieMiddleware(object):

    @staticmethod
    def process_response(request, response):
        try:
            if not request.session.get('counter_tracking', None):
                request.session['counter_tracking'] = str(uuid4())
            elif request.session.get('counter_tracking', None) and request.resolver_match.url_name == 'article_view':
                request.session.modified = True
        except AttributeError:
            pass

        return response


class PressMiddleware(object):

    @staticmethod
    def process_request(request):
        if request.journal:
            # This middleware is for the press site only
            pass
        elif request.press:
            allowed_urls = [
                'core_manager', 'core_manager_news', 'core_manager_edit_news', 'core_news_list', 'core_news_item',
                'news_file_download', 'core_flush_cache', 'core_login', 'core_login_orcid', 'core_register',
                'core_confirm_account', 'core_orcid_registration', 'core_get_reset_token', 'core_reset_password',
                'core_edit_profile', 'core_logout', 'press_cover_download', 'core_manager_index',
                'django_summernote-editor', 'django_summernote-upload_attachment', 'cms_index', 'cms_page_new',
                'cms_page_edit', 'cms_page', 'cms_nav', 'website_index', 'core_journal_contacts',
                'core_journal_contact', 'core_journal_contacts_order', 'contact', 'core_edit_settings_group',
            ]
            allowed_pattern = 'press_'

            if request.resolver_match:
                url_name = request.resolver_match.url_name

                if not url_name:
                    pass
                else:
                    if url_name in allowed_urls or url_name.startswith(allowed_pattern):
                        pass
                    else:
                        raise Http404('Press cannot access this page.')


class GlobalRequestMiddleware(object):
    _threadmap = {}

    @classmethod
    def get_current_request(cls):
        return cls._threadmap[thread.get_ident()]

    def process_request(self, request):
        self._threadmap[thread.get_ident()] = request

    def process_exception(self, request, exception):
        try:
            del self._threadmap[thread.get_ident()]
        except KeyError:
            pass

    def process_response(self, request, response):
        try:
            del self._threadmap[thread.get_ident()]
        except KeyError:
            pass
        return response
