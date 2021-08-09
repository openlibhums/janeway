__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from utils import setting_handler, models
from utils.logger import get_logger

logger = get_logger(__name__)


def yield_homepage_element_context(request, homepage_elements):
    plugin = models.Plugin.objects.get(name='HTML')
    try:
        html_block_content = setting_handler.get_plugin_setting(plugin, 'html_block_content', request.journal).value
    except AttributeError as e:
        logger.exception(e)
        html_block_content = '<p>This element has no content.</p>'

    return {'html_content': html_block_content}
