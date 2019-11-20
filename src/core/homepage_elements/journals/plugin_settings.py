__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.db.utils import OperationalError
from django.contrib.contenttypes.models import ContentType

PLUGIN_NAME = 'Journals'
DESCRIPTION = 'This plugin displays featured journals.'


def install():
    import core.models as core_models
    import press.models as press_models

    presses = press_models.Press.objects.all()

    for press in presses:
        content_type = ContentType.objects.get_for_model(press)
        element, created = core_models.HomepageElement.objects.get_or_create(
            name=PLUGIN_NAME,
            configure_url='featured_journals',
            template_path='journal/homepage_elements/journals.html',
            content_type=content_type,
            object_id=press.pk,
            has_config=True,
            available_to_press=True)

        element.save()


def hook_registry():
    try:
        install()
        return {
            'yield_homepage_element_context': {
                'module': 'core.homepage_elements.journals.hooks',
                'function': 'yield_homepage_element_context',
                'name': PLUGIN_NAME,
            }
        }
    except OperationalError:
        # if we get here the database hasn't yet been created
        return {}
    except:
        return {}
