from django.db.utils import OperationalError
from django.db.utils import ProgrammingError
from django.contrib.contenttypes.models import ContentType

from utils import models, setting_handler

PLUGIN_NAME = 'Search Bar'
SHORT_NAME = 'search_bar'
DESCRIPTION = 'This is a homepage element that renders a search bar.'
AUTHOR = 'Mauro Sanchez'
VERSION = '1.0'


def install():
    import core.models as core_models
    import journal.models as journal_models
    import press.models as press_models

    # check whether this homepage element has already been installed for all journals
    journals = journal_models.Journal.objects.all()
    plugin, created = models.Plugin.objects.get_or_create(
        name=PLUGIN_NAME,
        defaults=dict(
            version=VERSION,
            enabled=True,
            display_name='Search Bar',
            press_wide=True,
            homepage_element=True,
        )
    )
    for journal in journals:
        content_type = ContentType.objects.get_for_model(journal)
        element, created = core_models.HomepageElement.objects.update_or_create(
            name=PLUGIN_NAME,
            content_type=content_type,
            object_id=journal.pk,
            defaults=dict(
                configure_url=None,
                template_path='core/homepage_elements/search_bar.html',
                has_config=False,
                available_to_press=False,
            )
        )

        element.save()

    presses = press_models.Press.objects.all()

    for press in presses:
        content_type = ContentType.objects.get_for_model(press)
        element, created = core_models.HomepageElement.objects.update_or_create(
            name=PLUGIN_NAME,
            content_type=content_type,
            object_id=press.pk,
            defaults=dict(
                configure_url=None,
                template_path='core/homepage_elements/search_bar.html',
                has_config=False,
                available_to_press=False,
            ),
        )

        element.save()


def hook_registry():
    try:
        return {
            'yield_homepage_element_context': {
                'module': 'core.homepage_elements.search_bar.hooks',
                'function': 'yield_homepage_element_context',
                'name': PLUGIN_NAME,
            }
        }
    except (OperationalError, ProgrammingError):
        # if we get here the database hasn't yet been created
        return {}
