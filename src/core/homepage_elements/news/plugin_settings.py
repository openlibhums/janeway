from django.db.utils import OperationalError
from django.contrib.contenttypes.models import ContentType

from utils import models

PLUGIN_NAME = 'News'
SHORT_NAME = 'news'
DESCRIPTION = 'This is a homepage element that renders News section.'
AUTHOR = 'Martin Paul Eve & Andy Byers'
VERSION = '1.0'


def install():
    import core.models as core_models
    import journal.models as journal_models
    import press.models as press_models

    # check whether this homepage element has already been installed for all journals
    journals = journal_models.Journal.objects.all()

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

    models.Plugin.objects.get_or_create(
        name=PLUGIN_NAME,
        version=VERSION,
        enabled=True,
        display_name='News',
        press_wide=True,
    )


def hook_registry():
    try:
        install()
        return {'yield_homepage_element_context': {'module': 'core.homepage_elements.news.hooks',
                                                   'function': 'yield_homepage_element_context'}
                }
    except OperationalError:
        # if we get here the database hasn't yet been created
        return {}
    except BaseException:
        return {}
