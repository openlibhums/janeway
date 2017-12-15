from django.db.utils import OperationalError
from django.contrib.contenttypes.models import ContentType

PLUGIN_NAME = 'Current Issue'
DESCRIPTION = 'This is a homepage element that renders featured current issues.'
AUTHOR = 'Martin Paul Eve'


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
            configure_url='current_issue_setup',
            template_path='journal/homepage_elements/issue_block.html',
            content_type=content_type,
            object_id=journal.pk,
            has_config=True)

        element.save()

    presses = press_models.Press.objects.all()

    for press in presses:
        content_type = ContentType.objects.get_for_model(press)
        element, created = core_models.HomepageElement.objects.get_or_create(
            name=PLUGIN_NAME,
            configure_url='current_issue_setup',
            template_path='journal/homepage_elements/issue_block.html',
            content_type=content_type,
            object_id=press.pk,
            has_config=True)

        element.save()


def hook_registry():
    try:
        install()
        return {'yield_homepage_element_context': {'module': 'core.homepage_elements.featured.hooks',
                                                   'function': 'yield_homepage_element_context'}
                }
    except OperationalError:
        # if we get here the database hasn't yet been created
        return {}
    except BaseException:
        return {}
