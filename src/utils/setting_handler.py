__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import json
import os
import codecs

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils import translation

from core import models as core_models
from utils import models
from utils.logger import get_logger

logger = get_logger(__name__)


def create_setting(
        setting_group_name,
        setting_name,
        type,
        pretty_name,
        description,
        is_translatable=True,
        default_value=None,
):
    # If the setting is translatable use current lang, else use the default.
    lang = translation.get_language() if is_translatable else settings.LANGUAGE_CODE

    with translation.override(lang):
        group, c = core_models.SettingGroup.objects.get_or_create(
            name=setting_group_name,
        )
        new_setting, created = core_models.Setting.objects.get_or_create(
            group=group,
            name=setting_name,
            defaults={
                'types': type,
                'pretty_name': pretty_name,
                'description': description,
                'is_translatable': is_translatable,
            }
        )

        if created and default_value:
            core_models.SettingValue.objects.get_or_create(
                setting=new_setting,
                value=default_value,
            )

        return new_setting


def get_or_create_default_setting(setting, default_value):
    """
    Creates a setting linked to no journals, this is the default returned by
    get_setting.
    """
    setting, c = core_models.SettingValue.objects.get_or_create(
        setting=setting,
        journal=None,
        defaults={
            'value': default_value,
        }
    )

    return setting


def get_setting(
        setting_group_name,
        setting_name,
        journal,
        create=False,
        default=True,
):
    """
    Returns a matching SettingValue for the current language.

    If not journal is passed it returns the default setting directly. If
    default is True it will attempt t return the base language or the default value
    (in that order).
    :setting_group: (str) The group__name of the Setting
    :setting_name: (str) The name of the Setting
    :journal: (Journal object) The journal for which this setting is relevant.
        If None, returns the default value
    :create: If True, a journal override will be created if one is not present
    :default: If True, returns the default SettingValue when no journal specific
        value is present
    """
    try:
        setting = core_models.Setting.objects.get(
            name=setting_name,
            group__name=setting_group_name,
        )
    except ObjectDoesNotExist as e:
        e.args += (setting_name, setting_group_name)
        raise e
    lang = translation.get_language() if setting.is_translatable else settings.LANGUAGE_CODE

    with translation.override(lang):
        try:
            return core_models.SettingValue.objects.get(
                setting__group__name=setting_group_name,
                setting=setting,
                journal=journal,
            )
        except ObjectDoesNotExist as e:
            if journal is not None:
                if create:
                    logger.warning(
                        "Passing 'create' to get_setting has been deprecated in "
                        "in favour of returning the default value"
                    )
                if default or create:
                    # return press wide setting
                    journal = None
                    return get_setting(
                        setting_group_name,
                        setting,
                        journal,
                        create,
                    )
                else:
                    return None
            else:
                e.args += (setting_name, setting_group_name)
                raise e


def get_requestless_setting(setting_group, setting, journal):
    logger.warning(
        "Function get_requestless_setting is deprecated in v1.4 "
        "as ModelTranslations does not require a request/response cycle."
    )
    return get_setting(
        setting_group,
        setting,
        journal,
    )


def save_setting(setting_group_name, setting_name, journal, value):
    setting = core_models.Setting.objects.get(
        name=setting_name,
        group__name=setting_group_name,
    )
    lang = translation.get_language() if setting.is_translatable else settings.LANGUAGE_CODE

    with translation.override(lang):
        setting_value, created = core_models.SettingValue.objects \
            .get_or_create(
                setting__group=setting.group,
                setting=setting,
                journal=journal
        )

        if created:
            # Ensure that a value exists for settings.LANGUAGE_CODE
            setattr(setting, 'value_{0}'.format(settings.LANGUAGE_CODE), '')
            setting_value.save()

        if setting.types == 'json' and isinstance(value, (list, dict)):
            value = json.dumps(value)

        if setting.types == 'boolean':
            value = 'on' if value else ''

        setting_value.value = value
        setting_value.save()

        return setting_value


def save_plugin_setting(plugin, setting_name, value, journal):
    plugin_group_name = 'plugin:{plugin_name}'.format(plugin_name=plugin.name)
    setting = save_setting(
        setting_group_name=plugin_group_name,
        setting_name=setting_name,
        journal=journal,
        value=value,
    )
    return setting


def get_plugin_setting(
        plugin,
        setting_name,
        journal,
        create=False,
        pretty='',
        types='Text,'
):
    plugin_group_name = 'plugin:{plugin_name}'.format(plugin_name=plugin.name)
    try:
        return get_setting(
            setting_group_name=plugin_group_name,
            setting_name=setting_name,
            journal=journal,
            create=False,
            default=True,
        )
    except core_models.Setting.DoesNotExist as e:
        if create:
            setting = create_setting(
                setting_group_name=plugin_group_name,
                setting_name=setting_name,
                type=types,
                pretty_name=pretty,
                description='',
                is_translatable=False,
            )

            return setting

    except core_models.Setting.MultipleObjectsReturned as e:
        logger.error("Found multiple {}".format(setting_name, plugin_group_name))

        raise e


def get_email_subject_setting(
        setting_group,
        setting_name,
        journal,
        default=True,
):
    try:
        setting = core_models.Setting.objects.get(name=setting_name)
        return get_setting(setting_group, setting, journal, create=False, default=True).value
    except (core_models.Setting.DoesNotExist, AttributeError):
        return setting_name


def toggle_boolean_setting(setting_name, setting_group_name, journal):
    setting_value = get_setting(
        setting_group_name,
        setting_name,
        journal,
    )

    if setting_value.setting.types == "boolean":
        save_setting(
            setting_group_name=setting_group_name,
            setting_name=setting_name,
            journal=journal,
            value=False if setting_value.processed_value else True,
        )


def fetch_defaults_value(setting):
    with codecs.open(os.path.join(settings.BASE_DIR, 'utils/install/journal_defaults.json'), 'r+', encoding='utf-8') as json_data:
        default_data = json.load(json_data)
        for item in default_data:
            if item['setting']['name'] == setting.get('name'):
                return item['value']['default']


def update_settings(settings_to_change, journal):
    print('Updating {journal} settings... '.format(journal=journal.code))
    for setting in settings_to_change:

        try:
            setting_object = get_setting(setting.get('group'), setting.get('name'), journal)

            if setting.get('action', None) == 'update':
                print('Updating {setting}, action: {action}'.format(setting=setting.get('name'),
                                                                    action=setting.get('action')))
                check = input('If you want to update this setting, respond with y: ')
                if check == 'y':
                    defaults_value = fetch_defaults_value(setting)
                    setting_object.value = defaults_value
                    setting_object.save()
            elif setting.get('action', None) == 'drop':
                setting_object.delete()
        except BaseException as e:
            print(e)
