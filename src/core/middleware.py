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


def match_by_domain(request):
    journal = repository = press = None
    try:
        journal = journal_models.Journal.get_by_request(request)
        press = journal.press
    except (journal_models.Journal.DoesNotExist, IndexError):
        try:
            repository = repository_models.Repository.get_by_request(request)
            press = repository.press
        except (repository_models.Repository.DoesNotExist, IndexError):
            pass

    return journal, repository, press


def match_by_path(request):
    journal = repository = press = None
    code = request.path.split('/')[1]
    try:
        journal = journal_models.Journal.objects.get(
            code=code,
            use_domain_mode=False,
        )
        press = journal.press
    except (journal_models.Journal.DoesNotExist, IndexError):
        try:
            repository = repository_models.Repository.objects.get(
                short_name=code,
                use_domain_mode=False,
            )
            press = repository.press
        except (repository_models.Repository.DoesNotExist, IndexError):
            pass

    return journal, repository, press


def get_site_resources(request):
    """
    Attempts to match the relevant resource for the request URL.
    Checks in the following order:
    - Journal
    - Repository
    - Press
    """
    journal = repository = press = redirect_obj = None

    # Check for domain matches
    journal, repository, press = match_by_domain(request)

    # If none are found: check for path matches
    if not journal and not repository:
        journal, repository, press = match_by_path(request)

    # if we still don't have a match: check if the press has a domain match.
    if not journal and not repository:
        press = press_models.Press.get_by_request(request)

    if not journal and not repository and not press:
        try:  # try alias
            alias = core_models.DomainAlias.get_by_request(request)
            if alias.redirect:
                logger.debug("Matched a redirect: %s" % alias.redirect_url)
                redirect_obj = redirect(alias.redirect_url)
            else:
                if alias.journal:
                    journal = alias.journal
                    press = journal.press
                elif alias.repository:
                    repository = alias.repository
                    press = repository.press
                elif alias.press:
                    press = alias.press

        except core_models.DomainAlias.DoesNotExist:
            # Give up
            logger.warning(
                "Couldn't match a resource for %s, redirecting to %s"
                "" % (request.path, settings.DEFAULT_HOST)
            )
            redirect_obj = redirect(settings.DEFAULT_HOST)

    print(journal, repository, press, redirect_obj)

    return journal, repository, press, redirect_obj


class SiteSettingsMiddleware(object):
    @staticmethod
    def process_request(request):
        """ This middleware class sets a series of variables for templates
        and views to access inside the request object. It defines what site
        is being requested based on the domain:

        if settings.URL_CONFIG is set to 'domain':
            matches alias, journal, press  models by domain (in that order)
        if settings.URL_CONFIG is set to 'domain':
            matches the press by domain and journal by path. If no journal code
            is present it assumes a press site.

        :param request: the current request
        :return: None or an http 404 error in the event of catastrophic failure
        """

        journal, repository, press, redirect_obj = get_site_resources(request)

        if redirect_obj is not None:
            return redirect_obj

        request.port = request.META['SERVER_PORT']
        request.press = press
        request.press_cover = press.press_cover(request)

        if journal is not None:
            logger.set_prefix(journal.code)
            request.journal = journal
            request.journal_cover = journal.override_cover(request)
            request.site_type = journal
            request.model_content_type = ContentType.objects.get_for_model(
                    journal)
            request.repository = None

            if not request.site_type.use_domain_mode:
                prefix = "/" + journal.code
                logger.debug("Setting script prefix to %s" % prefix)
                set_script_prefix(prefix)
                request.path_info = request.path_info[len(prefix):]

        elif repository is not None:
            logger.set_prefix(repository.short_name)
            request.repository = repository
            request.journal = None
            request.site_type = repository
            request.model_content_type = ContentType.objects.get_for_model(
                repository,
            )

            if not request.site_type.use_domain_mode:
                prefix = "/" + repository.short_name
                logger.debug("Setting script prefix to %s" % prefix)
                set_script_prefix(prefix)
                request.path_info = request.path_info[len(prefix):]

        elif press is not None:
            logger.set_prefix("press")
            request.journal = None
            request.repository = None
            request.site_type = press
            request.model_content_type = ContentType.objects.get_for_model(press)
            request.press_base_url = press.site_url()
        else:
            raise Http404()

        # We check if the journal and press are set to be secure and redirect if the current request is not secure.
        if not request.is_secure():
            if (
                    request.journal
                    and request.journal.is_secure
                    and not settings.DEBUG
            ):
                return redirect("https://{0}{1}".format(request.get_host(), request.path))
            elif request.press.is_secure and not settings.DEBUG:
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

