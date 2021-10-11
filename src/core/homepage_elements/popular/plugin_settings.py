from django.db.utils import OperationalError
from django.contrib.contenttypes.models import ContentType

from utils import models, setting_handler
from utils.logger import get_logger

logger = get_logger(__name__)

PLUGIN_NAME = 'Popular Articles'
SHORT_NAME = 'popular_articles'
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

    plugin_group_name = 'plugin:{plugin_name}'.format(plugin_name=PLUGIN_NAME)

    setting = setting_handler.create_setting(
        setting_group_name=plugin_group_name,
        setting_name='most_popular',
        type='boolean',
        pretty_name='Display Most Popular Articles',
        description='Displays the most popular articles.',
        is_translatable=False,
    )
    setting_handler.get_or_create_default_setting(
        setting=setting,
        default_value='',
    )
    setting = setting_handler.create_setting(
        setting_group_name=plugin_group_name,
        setting_name='num_most_popular',
        type='number',
        pretty_name='Number of Most Popular Articles to Display',
        description='Determines how many popular articles we should display.',
        is_translatable=False,
    )
    setting_handler.get_or_create_default_setting(
        setting=setting,
        default_value=3,
    )
    setting = setting_handler.create_setting(
        setting_group_name=plugin_group_name,
        setting_name='most_popular_time',
        type='text',
        pretty_name='Most Popular Timescale',
        description='Select from this week, this month or this year.',
        is_translatable=False,
    )
    setting_handler.get_or_create_default_setting(
        setting=setting,
        default_value='weekly',
    )

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
