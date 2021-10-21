__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from core import models as core_models
from utils import setting_handler, models
from utils.logger import get_logger

logger = get_logger(__name__)


def yield_homepage_element_context(request, homepage_elements):
    plugin = models.Plugin.objects.get(name='HTML')

    additional_html_hpes = core_models.HomepageElement.objects.filter(
        content_type=request.model_content_type,
        object_id=request.site_type.pk,
        active=True,
        name__startswith='html_',
    )

    context = {}

    try:
        html_block_content = setting_handler.get_plugin_setting(plugin, 'html_block_content', request.journal).value
    except AttributeError as e:
        logger.exception(e)
        html_block_content = '<p>This element has no content.</p>'

    context['html_content'] = html_block_content

    for additional_hpe in additional_html_hpes:
        setting_value = setting_handler.get_plugin_setting(
            plugin,
            additional_hpe.name,
            request.journal,
        ).value
        context[additional_hpe.name] = setting_value

    return context
