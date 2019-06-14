__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.db.utils import OperationalError
from django.contrib.contenttypes.models import ContentType

from utils import models
from utils.logger import get_logger

logger = get_logger(__name__)

PLUGIN_NAME = 'About'
DESCRIPTION = 'This is a homepage element that renders About this Journal section.'
AUTHOR = 'Martin Paul Eve & Andy Byers'
VERSION = '1.0'


def get_self():
    try:
        plugin = models.Plugin.objects.get(
            name=PLUGIN_NAME,
        )
        return plugin
    except models.Plugin.DoesNotExist:
        return None


def install():
    import core.models as core_models
    import journal.models as journal_models

    plugin, c = models.Plugin.objects.get_or_create(
        name=PLUGIN_NAME,
        version=VERSION,
        enabled=True,
        display_name='About',
    )

    if c:
        logger.debug('Plugin installed.')

    setting, c = models.PluginSetting.objects.get_or_create(
        name='about_title',
        plugin=plugin,
        defaults={
            'pretty_name': 'About Block Title',
            'types': 'text',
            'description': 'Sets the title of the About Block',
            'is_translatable': True,
        }
    )

    if c:
        logger.debug('Setting created')

    # check whether this homepage element has already
    # been installed for all journals
    journals = journal_models.Journal.objects.all()

    for journal in journals:
        content_type = ContentType.objects.get_for_model(journal)
        element, created = core_models.HomepageElement.objects.get_or_create(
            name=PLUGIN_NAME,
            configure_url='journal_description',
            template_path='journal/homepage_elements/about.html',
            content_type=content_type,
            object_id=journal.pk,
            has_config=True)

        element.save()


def hook_registry():
    try:
        return {'yield_homepage_element_context': {'module': 'core.homepage_elements.about.hooks',
                                                   'function': 'yield_homepage_element_context'}
                }
    except OperationalError:
        # if we get here the database hasn't yet been created
        return {}
    except BaseException:
        return {}
