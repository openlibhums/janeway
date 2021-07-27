__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.db.utils import OperationalError
from django.contrib.contenttypes.models import ContentType

from utils import models, setting_handler

PLUGIN_NAME = 'HTML'
DESCRIPTION = 'This is a homepage element that renders an HTML block'
AUTHOR = 'Andy Byers'
VERSION = 1.0


def install():
    import core.models as core_models
    import journal.models as journal_models
    import press.models as press_models

    plugin, c = models.Plugin.objects.get_or_create(
        name=PLUGIN_NAME,
        version=VERSION,
        enabled=True,
        display_name='HTML',
        press_wide=True,
        homepage_element=True,
    )
    plugin_group_name = 'plugin:{plugin_name}'.format(plugin_name=plugin.name)
    setting_group, c = core_models.SettingGroup.objects.get_or_create(
        name=plugin_group_name,
    )
    setting, c = core_models.Setting.objects.get_or_create(
        name='html_block_content',
        group=setting_group,
        defaults={
            'pretty_name': 'HTML Block Content',
            'types': 'rich-text',
            'description': DESCRIPTION,
            'is_translatable': True,
        }
    )

    # check whether this homepage element has
    # already been installed for all journals
    journals = journal_models.Journal.objects.all()

    for journal in journals:
        content_type = ContentType.objects.get_for_model(journal)
        element, created = core_models.HomepageElement.objects.get_or_create(
            name=PLUGIN_NAME,
            configure_url='html_settings',
            template_path='journal/homepage_elements/html_block.html',
            content_type=content_type,
            object_id=journal.pk,
            has_config=True)

        element.save()

    presses = press_models.Press.objects.all()

    for press in presses:
        content_type = ContentType.objects.get_for_model(press)
        element, created = core_models.HomepageElement.objects.get_or_create(
            name=PLUGIN_NAME,
            configure_url='html_settings',
            template_path='journal/homepage_elements/html_block.html',
            content_type=content_type,
            object_id=press.pk,
            has_config=True,
            available_to_press=True)

        element.save()


def hook_registry():
    try:
        return {'yield_homepage_element_context': {'module': 'core.homepage_elements.html.hooks',
                                                   'function': 'yield_homepage_element_context',
                                                   'name': PLUGIN_NAME,}
                }
    except OperationalError:
        # if we get here the database hasn't yet been created
        return {}
    except BaseException:
        return {}
