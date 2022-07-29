__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.utils.translation import ugettext_lazy as _

from utils.setting_handler import get_plugin_setting
from core.homepage_elements.about import plugin_settings


def yield_homepage_element_context(request, homepage_elements):
    if homepage_elements is not None and homepage_elements.filter(name='About').exists():

        try:
            title = get_plugin_setting(
                plugin_settings.get_self(),
                'about_title',
                request.journal,
            )
            title_value = title.value if title.value else ''
        except AttributeError:
            title_value = _('About this Journal')

        return {
            'about_content': request.journal.description,
            'title_value': title_value,
        }
    else:
        return {}
