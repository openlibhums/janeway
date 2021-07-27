from django.db.utils import OperationalError
from django.db.utils import ProgrammingError
from django.contrib.contenttypes.models import ContentType

from utils import models, setting_handler

PLUGIN_NAME = 'News'
SHORT_NAME = 'news'
DESCRIPTION = 'This is a homepage element that renders News section.'
AUTHOR = 'Martin Paul Eve & Andy Byers'
VERSION = '1.0'
DEFAULT_NEWS = 5  # Defines how many news are to be displayed by default


def install():
    import core.models as core_models
    import journal.models as journal_models
    import press.models as press_models

    # check whether this homepage element has already been installed for all journals
    journals = journal_models.Journal.objects.all()
    plugin, created = models.Plugin.objects.get_or_create(
        name=PLUGIN_NAME,
        version=VERSION,
        enabled=True,
        display_name='News',
        press_wide=True,
        homepage_element=True,
    )
    plugin_group_name = 'plugin:{plugin_name}'.format(plugin_name=plugin.name)
    setting = setting_handler.create_setting(
        setting_group_name=plugin_group_name,
        setting_name='number_of_articles',
        type='number',
        pretty_name='Number of Articles',
        description='Number of news articles to display on the homepage.',
        is_translatable=False,
    )
    setting_handler.get_or_create_default_setting(
        setting,
        default_value=DEFAULT_NEWS,
    )

    for journal in journals:
        content_type = ContentType.objects.get_for_model(journal)
        element, created = core_models.HomepageElement.objects.get_or_create(
            name=PLUGIN_NAME,
            configure_url='news_config',
            template_path='journal/homepage_elements/news.html',
            content_type=content_type,
            object_id=journal.pk,
            has_config=True,
            defaults={'available_to_press': True})

        element.save()

        number_of_articles = setting_handler.get_plugin_setting(
            plugin=plugin,
            setting_name='number_of_articles',
            journal=journal,
            create=True,
            pretty='Number of Articles',
        )
        if number_of_articles in {None, " ", ""}:
            setting_handler.save_plugin_setting(
                plugin=plugin,
                setting_name='number_of_articles',
                value=DEFAULT_NEWS,
                journal=journal,
            )

    presses = press_models.Press.objects.all()

    for press in presses:
        content_type = ContentType.objects.get_for_model(press)
        element, created = core_models.HomepageElement.objects.get_or_create(
            name=PLUGIN_NAME,
            configure_url='news_config',
            template_path='journal/homepage_elements/news.html',
            content_type=content_type,
            object_id=press.pk,
            has_config=True,
            defaults={'available_to_press': True})

        element.save()


def hook_registry():
    try:
        return {
            'yield_homepage_element_context': {
                'module': 'core.homepage_elements.news.hooks',
                'function': 'yield_homepage_element_context',
                'name': PLUGIN_NAME,
            }
        }
    except (OperationalError, ProgrammingError):
        # if we get here the database hasn't yet been created
        return {}
