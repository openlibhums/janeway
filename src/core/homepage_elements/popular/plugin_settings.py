from django.db.utils import OperationalError
from django.contrib.contenttypes.models import ContentType

from utils import models
from utils.logger import get_logger

logger = get_logger(__name__)

PLUGIN_NAME = 'Popular Articles'
DESCRIPTION = 'This is a homepage element that renders popular articles.'
AUTHOR = 'Martin Paul Eve'
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
        display_name='Popular Articles',
        homepage_element=True,
    )

    if c:
        logger.debug('Plugin {} created'.format(PLUGIN_NAME))

    models.PluginSetting.objects.get_or_create(
        name='most_popular',
        plugin=plugin,
        defaults={
            'pretty_name': 'Display Most Popular Articles',
            'types': 'boolean',
            'description': 'Displays the most popular articles.',
            'is_translatable': False,
        }
    )

    models.PluginSetting.objects.get_or_create(
        name='num_most_popular',
        plugin=plugin,
        defaults={
            'pretty_name': 'Number of Most Popular Articles to Display',
            'types': 'number',
            'description': 'Determines how many popular articles we should display.',
            'is_translatable': False,
        }
    )

    models.PluginSetting.objects.get_or_create(
        name='most_popular_time',
        plugin=plugin,
        defaults={
            'pretty_name': 'Most Popular Timescale',
            'types': 'text',
            'description': 'Select from this week, this month or this year.',
            'is_translatable': False,
        }
    )

    if c:
        logger.debug('Setting created')

    # check whether this homepage element has already been installed for all journals
    journals = journal_models.Journal.objects.all()

    for journal in journals:
        content_type = ContentType.objects.get_for_model(journal)
        element, created = core_models.HomepageElement.objects.get_or_create(
            name=PLUGIN_NAME,
            configure_url='popular_articles_setup',
            template_path='journal/homepage_elements/popular.html',
            content_type=content_type,
            object_id=journal.pk,
            has_config=True,
        )

        element.save()


def hook_registry():
    try:
        install()
        return {
            'yield_homepage_element_context': {
                'module': 'core.homepage_elements.popular.hooks',
                'function': 'yield_homepage_element_context',
                'name': PLUGIN_NAME,
            }
        }
    except OperationalError:
        # if we get here the database hasn't yet been created
        return {}
    except BaseException:
        return {}
