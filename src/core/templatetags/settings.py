from django import template

from core import models
from utils import setting_handler

register = template.Library()


def get_setting(journal, setting_name):
    try:
        setting_obj = models.Setting.objects.get(name=setting_name)
        setting_value = setting_handler.get_setting(
            setting_obj.group.name,
            setting_obj.name,
            journal,
        ).processed_value
        return setting_value
    except models.Setting.DoesNotExist:
        return ''


@register.filter
def setting(journal, setting_name):
    """
    Gets journal settings. Usage:

    {% load settings %}

    {{ request.journal|setting:'a_setting_name' }}
    """
    return get_setting(journal, setting_name)


@register.simple_tag
def setting_var(journal, setting_name):
    """
    Gets a journal setting. Usage:
    {% load settings %]

    {% setting_var request.journal 'setting_name' as setting_name %}
    {{ setting_name }}
    """
    return get_setting(journal, setting_name)
