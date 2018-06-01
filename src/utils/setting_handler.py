__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import json

from django.conf import settings
from django.utils.translation import get_language

from utils import models
from core import models as core_models


def create_setting(setting_group, setting_name, type, pretty_name, description, is_translatable=True):
    group = core_models.SettingGroup.objects.get(name=setting_group)
    new_setting, created = core_models.Setting.objects.get_or_create(
        group=group,
        name=setting_name,
        defaults={'types': type, 'pretty_name': pretty_name, 'description': description,
                  'is_translatable': is_translatable}
    )

    return new_setting


def get_setting(setting_group, setting_name, journal, create=False, fallback=False):
    setting = core_models.Setting.objects.get(name=setting_name)
    lang = get_language() if setting.is_translatable else 'en'

    return _get_setting(setting_group, setting, journal, lang, create, fallback)


def get_requestless_setting(setting_group, setting, journal):
    lang = settings.LANGUAGE_CODE
    setting = core_models.Setting.objects.get(name=setting)
    setting = core_models.SettingValue.objects.language(lang).get(
        setting__group__name=setting_group,
        setting=setting,
        journal=journal
    )

    return setting


def _get_setting(setting_group, setting, journal, lang, create, fallback):
    try:
        setting = core_models.SettingValue.objects.language(lang).get(
            setting__group__name=setting_group,
            setting=setting,
            journal=journal
        )
        return setting
    except core_models.SettingValue.DoesNotExist:
        if lang == settings.LANGUAGE_CODE:
            if create:
                return save_setting(setting_group, setting.name, journal, ' ')
            else:
                raise IndexError('Setting does not exist and will not be created.')
        else:
            # Switch get the setting and start a translation
            setting = core_models.SettingValue.objects.language(settings.LANGUAGE_CODE).get(
                setting__group__name=setting_group,
                setting=setting,
                journal=journal
            )

            if not fallback:
                setting.translate(lang)
            return setting


def save_setting(setting_group, setting_name, journal, value):
    setting = core_models.Setting.objects.get(name=setting_name)
    lang = get_language() if setting.is_translatable else 'en'

    setting_value, created = core_models.SettingValue.objects.language(lang).get_or_create(
        setting__group=setting.group,
        setting=setting,
        journal=journal
    )

    if setting.types == 'json':
        value = json.dumps(value)

    if setting.types == 'boolean':
        value = 'on' if value else ''

    setting_value.value = value

    setting_value.save()

    return setting_value


def save_plugin_setting(plugin, setting_name, value, journal):
    setting = models.PluginSetting.objects.get(name=setting_name)
    lang = get_language() if setting.is_translatable else 'en'

    setting_value, created = models.PluginSettingValue.objects.language(lang).get_or_create(
        setting__plugin=plugin,
        setting=setting,
        journal=journal
    )

    if setting.types == 'json':
        value = json.dumps(value)

    if setting.types == 'boolean':
        value = 'on' if value else ''

    setting_value.value = value

    setting_value.save()

    return setting_value


def get_plugin_setting(plugin, setting_name, journal, create=False, pretty='', fallback='', types='Text'):
    if not create:
        setting = models.PluginSetting.objects.get(name=setting_name, plugin=plugin)
    else:
        setting, created = models.PluginSetting.objects.get_or_create(name=setting_name,
                                                                      plugin=plugin,
                                                                      types=types,
                                                                      defaults={'pretty_name': pretty,
                                                                                'types': types})

        if created:
            save_plugin_setting(plugin, setting_name, ' ', journal)

    lang = get_language() if setting.is_translatable else 'en'

    return _get_plugin_setting(plugin, setting, journal, lang, create, fallback)


def _get_plugin_setting(plugin, setting, journal, lang, create, fallback):
    try:
        setting = models.PluginSettingValue.objects.language(lang).get(
            setting__plugin=plugin,
            setting=setting,
            journal=journal
        )
        return setting
    except models.PluginSettingValue.DoesNotExist:
        if lang == settings.LANGUAGE_CODE:
            if create:
                return save_plugin_setting(plugin, setting.name, '', journal)
            else:
                raise IndexError('Plugin setting does not exist and will not be created.')
        else:
            # Switch get the setting and start a translation
            setting = models.PluginSettingValue.objects.language(settings.LANGUAGE_CODE).get(
                setting__plugin=plugin,
                setting=setting,
                journal=journal
            )

            if not fallback:
                setting.translate(lang)
            return setting


def get_email_subject_setting(setting_group, setting_name, journal, create=False, fallback=False):
    try:
        setting = core_models.Setting.objects.get(name=setting_name)
        lang = get_language() if setting.is_translatable else 'en'

        return _get_setting(setting_group, setting, journal, lang, create, fallback).value
    except core_models.Setting.DoesNotExist:
        return setting_name


def update_settings(settings_to_change, journal):
    for setting in settings_to_change:

        setting_object = get_setting(setting.get('group'), settings.get('name'), journal)

        if setting.get('action', None) == 'update':
            pass
        elif setting.get('action', None) == 'drop':
            setting_object.delete()
