__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from uuid import uuid4
import threading

import pytz

from django.core.exceptions import ObjectDoesNotExist, \
    MultipleObjectsReturned, ImproperlyConfigured
from django.http import Http404
from django.core.exceptions import PermissionDenied
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import redirect
from django.conf import settings
from django.urls import set_script_prefix
from django.utils import timezone

from press import models as press_models
from utils import models as util_models, setting_handler
from utils.logger import get_logger
from core import models as core_models
from journal import models as journal_models
from repository import models as repository_models

logger = get_logger(__name__)


def get_site_resources(request):
    """ Attempts to match the relevant resources for the request url

    Each site type is given a chance to resolve the url by domain or path
    :param request: A Django HttpRequest
    :return: press.models.Press,journal.models.Journal,HttpResponseRedirect
    """
    # Match a journal
    journal = repository = press = redirect_obj = site_path = None
    journal, site_path = journal_models.Journal.get_by_request(request)
    if journal:
        press = journal.press
    else:
        # Match a Repository
        repository, site_path = repository_models.Repository.get_by_request(request)
        if repository:
            press = repository.press
        else:
            # Match the press site
            press, path_mode = press_models.Press.get_by_request(request)

    # Match a Domain Alias
    if not press:
        alias, site_path = core_models.DomainAlias.get_by_request(request)
        if alias and alias.redirect:
            logger.debug("Matched a redirect: %s" % alias.redirect_url)
            redirect_obj = redirect(
                alias.build_redirect_url(path=request.path))
        elif alias:
            journal = alias.journal
            press = journal.press if journal else alias.press


    #  Couldn't match any resources
    if not press and not redirect_obj:
        logger.warning(
            "Couldn't match a resource for %s, redirecting to default: %s"
            "" % (request.path, settings.DEFAULT_HOST)
            )
        redirect_obj = redirect(settings.DEFAULT_HOST)

    return journal, repository, press, redirect_obj, site_path


class SiteSettingsMiddleware(object):
    @staticmethod
    def process_request(request):
        """ This middleware class sets a series of variables for templates
        and views to access inside the request object. It defines what site
        is being requested based on the domain and/or path

        :param request: the current request
        :return: None or an http 404 error in the event of catastrophic failure
        """

        journal, repository, press, redirect_obj, site_path = get_site_resources(
            request)

        if redirect_obj is not None:
            return redirect_obj

        request.port = request.META['SERVER_PORT']
        request.press = press
        request.press_cover = press.press_cover(request)

        if journal is not None:
            logger.set_prefix(journal.code)
            request.journal = journal
            request.journal_cover = journal.press_image_override.path if journal.press_image_override else None
            request.site_type = request.site_object = journal
            request.model_content_type = ContentType.objects.get_for_model(
                    journal)
            request.repository = None

        elif repository is not None:
            logger.set_prefix(repository.short_name)
            request.repository = repository
            request.journal = None
            request.site_type = request.site_object = repository
            request.model_content_type = ContentType.objects.get_for_model(
                repository,
            )

        elif press is not None:
            logger.set_prefix("press")
            request.journal = None
            request.repository = None
            request.site_type = request.site_object = press
            request.model_content_type = ContentType.objects.get_for_model(press)
            request.press_base_url = press.site_url()
        else:
            raise Http404()

        # Set the script prefix if the site is in path mode
        if site_path:
            prefix = "/" + site_path
            logger.debug("Setting script prefix to %s" % prefix)
            set_script_prefix(prefix)
            request.path_info = request.path_info[len(prefix):]

        # We check if the journal and press are set to be secure and redirect if the current request is not secure.
        if not request.is_secure():
            if (
                    request.site_object
                    and request.site_object.is_secure
                    and not settings.DEBUG
            ):
                return redirect("https://{0}{1}".format(request.get_host(), request.path))


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


_threadlocal = threading.local()


class GlobalRequestMiddleware(object):
    @classmethod
    def get_current_request(cls):
        return _threadlocal.request

    @staticmethod
    def process_request(request):
        _threadlocal.request = request


class TimezoneMiddleware(object):
    def process_request(self, request):
        if request.user.is_authenticated and request.user.preferred_timezone:
            tzname = request.user.preferred_timezone
        elif request.session.get("janeway_timezone"):
            tzname = request.session["janeway_timezone"]
        else:
            tzname = None
            request.timezone = None

        try:
            if tzname is not None:
                tzinfo = pytz.timezone(tzname)
                request.timezone = tzinfo
                timezone.activate(tzinfo)
                logger.debug("Activated timezone %s" % tzname)
        except Exception as e:
            logger.warning("Failed to activate timezone %s: %s" % (tzname, e))

