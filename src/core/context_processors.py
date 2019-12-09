__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.core.exceptions import ObjectDoesNotExist

from journal import models as journal_models
from press import models as press_models
from cms import models as cms_models
from core import logic


def journal(request):
    """
    This context processor injects the variable 'journal' into every request, corresponding to the currently accessed
    domain.

    :param request: the active request
    :return: dictionary containing a journal object under key 'journal' or None if this is a press site
    """
    return {'journal': request.journal}


def press(request):
    """
    This context processor injects the variable 'press' into every request, corresponding to the currently accessed
    domain.

    :param request: the active request
    :return: dictionary containing a press object under key 'press'
    """
    return {
        'press': request.press,
        'display_preprint_editors': request.press.get_setting_value(
            'Display Preprint Editors')
    }


def journal_settings(request):
    """
    This context processor injects the variable 'journal_settings' into every request, corresponding to the currently
    accessed domain.

    :param request: the active request
    :return: dictionary containing a dictionary of journal settings under key 'journal_settings'
    """

    return {'journal_settings': logic.settings_for_context(request)}


def active(request):
    """
    This context processor injects the variable 'active' into every request, corresponding to the currently accessed
    domain. It is used to highlight the currently active URL path in navigation menus.

    :param request: the active request
    :return: the active path that corresponds to this request or an empty string if at root
    """
    try:
        url_list = request.path.split('/')
        return {'active': url_list[1]}
    except (IndexError, AttributeError):
        return {'active': ''}


def navigation(request):
    """
    This context processor injects the navigation into the context for use generating a navigation

    :param request: the active request
    :return: the active path that corresponds to this request or an empty string if at root
    """
    top_nav_items = cms_models.NavigationItem.objects.filter(content_type=request.model_content_type,
                                                             object_id=request.site_type.pk,
                                                             top_level_nav__isnull=True).order_by('sequence')

    return {'navigation_items': top_nav_items}
