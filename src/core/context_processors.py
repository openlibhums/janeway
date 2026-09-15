__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.utils.encoding import force_str
from django.utils.safestring import mark_safe

from cms import models as cms_models
from core import logic, text_format
from utils.logic import get_janeway_version


def journal(request):
    """
    This context processor injects the variable 'journal' into every request, corresponding to the currently accessed
    domain.

    :param request: the active request
    :return: dictionary containing a journal object under key 'journal' or None if this is a press site
    """
    return {"journal": request.journal}


def press(request):
    """
    This context processor injects the variable 'press' into every request, corresponding to the currently accessed
    domain.

    :param request: the active request
    :return: dictionary containing a press object under key 'press'
    """
    return {
        "press": request.press,
        "display_preprint_editors": request.press.get_setting_value(
            "Display Preprint Editors"
        ),
    }


def journal_settings(request):
    """
    This context processor injects the variable 'journal_settings' into every request, corresponding to the currently
    accessed domain.

    :param request: the active request
    :return: dictionary containing a dictionary of journal settings under key 'journal_settings'
    """

    return {"journal_settings": logic.settings_for_context(request)}


def active(request):
    """
    This context processor injects the variable 'active' into every request, corresponding to the currently accessed
    domain. It is used to highlight the currently active URL path in navigation menus.

    :param request: the active request
    :return: the active path that corresponds to this request or an empty string if at root
    """
    try:
        url_list = request.path.split("/")
        return {"active": url_list[1]}
    except (IndexError, AttributeError):
        return {"active": ""}


def navigation(request):
    """
    This context processor injects the navigation into the context for use generating a navigation

    :param request: the active request
    :return: the active path that corresponds to this request or an empty string if at root
    """
    top_nav_items = cms_models.NavigationItem.objects.filter(
        content_type=request.model_content_type,
        object_id=request.site_type.pk,
        top_level_nav__isnull=True,
    ).order_by("sequence")

    return {"navigation_items": top_nav_items}


def version(request):
    """
    This context processor injects the Janeway version into the context for use in the sidebar.

    :param request: an HttpRequest object
    :return: a dictionary containing the current version.
    """
    return {"version": get_janeway_version()}


def accessibility_mode(request):
    """Expose the resolved accessibility-mode flag in template context."""
    return {"accessibility_mode_active": logic.accessibility_mode_active(request)}


def text_format_preferences(request):
    """Expose the reader's stored reading-options preferences to templates.

    ``text_format_initial_style`` is server-rendered CSS that paints the reading
    region in a restored colour scheme on first paint, so there is no flash of
    the default colour before text_readability.js runs. Safe: the helper only
    emits validated hex values.
    """
    preferences = logic.text_format_preferences(request)
    return {
        "text_format_preferences": preferences,
        "text_format_initial_style": mark_safe(
            text_format.initial_region_colour_css(preferences)
        ),
    }


def text_format_options(request):
    """Expose the reading-options registry (fonts, schemes, size bounds)."""

    def resolve(entries):
        return {
            slug: {**entry, "label": force_str(entry["label"])}
            for slug, entry in entries.items()
        }

    options = {
        "fonts": resolve(text_format.FONTS),
        "schemes": resolve(text_format.COLOUR_SCHEMES),
        "sizeBounds": text_format.DEFAULT_SIZE_BOUNDS,
        "strings": {
            key: force_str(value) for key, value in text_format.ANNOUNCEMENTS.items()
        },
    }
    return {"text_format_options": options}
