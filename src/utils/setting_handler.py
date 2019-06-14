__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import json
import os
import codecs

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management import call_command
from django.utils.translation import get_language

from core import models as core_models
from utils import models
from utils.logger import get_logger

logger = get_logger(__name__)


def create_setting(setting_group, setting_name, type, pretty_name, description, is_translatable=True):
    group = core_models.SettingGroup.objects.get(name=setting_group)
    new_setting, created = core_models.Setting.objects.get_or_create(
        group=group,
        name=setting_name,
        defaults={'types': type, 'pretty_name': pretty_name, 'description': description,
                  'is_translatable': is_translatable}
    )

    return new_setting


def get_setting(
        setting_group, setting_name,
        journal=None,
        create=False,
        fallback=True,
        default=True,
):
    """ Returns a matching SettingValue for the language in context

    It no journal is passed it returns the default setting directly. If
    fallback or default are True, it will attempt to returnthe base language
    and/or the default value respectively (in that order)
    :setting_group: (str) The group__name of the Setting
    :setting_name: (str) The name of the Setting
    :journal: (Journal object) The journal for which this setting is relevant.
        If None, returns the default value
    :create: If True, a journal override will be created if one is not present
    :fallback: If True, it will attempt to return the value for the base
        language when no value is available for the current language
    :default: If True, returns the default SettingValue when no journal specific
        value is present
    """
    setting = core_models.Setting.objects.get(name=setting_name)
    lang = get_language() if setting.is_translatable else settings.LANGUAGE_CODE
    try:
        return _get_setting(
            setting_group, setting, journal, lang, create, fallback, default)
    except Exception as e:
        logger.critical(
                "Failed to load setting for context:\n"
                "setting_name: {0},\n"
                "journal: {1},\n"
                "fallback: {2},\n"
                "request language: {3},\n"
                "settings language: {4},\n"
                "".format(
                    setting_name, journal, fallback,
                    lang, settings.LANGUAGE_CODE
                )
            )
        raise e


def get_requestless_setting(setting_group, setting, journal):
    lang = settings.LANGUAGE_CODE
    setting = core_models.Setting.objects.get(name=setting)
    setting = core_models.SettingValue.objects.language(lang).get(
        setting__group__name=setting_group,
        setting=setting,
        journal=journal
    )

    return setting


def _get_setting(
        setting_group,
        setting,
        journal,
        lang,
        create=False,
        fallback=True,
        default=True,
):
    if fallback:
        _fallback = settings.LANGUAGE_CODE
    else:
        _fallback = None # deactivates fallback

    try:
        return core_models.SettingValue.objects \
            .language(lang) \
            .fallbacks(_fallback) \
            .get(
                setting__group__name=setting_group,
                setting=setting,
                journal=journal,
        )
    except ObjectDoesNotExist:
        if journal is not None:
            if create:
                logger.warning(
                    "Passing 'create' to get_setting has been deprecated in "
                    "in favour of returning the default value"
                )
            if default or create:
                # return press wide setting
                journal = None
                return _get_setting(
                        setting_group, setting, journal,
                        lang, create, fallback,
                )
            else:
                return None
        else:
            raise


def save_setting(setting_group, setting_name, journal, value):
    setting = core_models.Setting.objects.get(name=setting_name)
    lang = get_language() if setting.is_translatable else settings.LANGUAGE_CODE

    setting_value, created = core_models.SettingValue.objects \
        .language(settings.LANGUAGE_CODE) \
        .get_or_create(
            setting__group=setting.group,
            setting=setting,
            journal=journal
    )

    if created:
        # Ensure that a value exists for settings.LANGUAGE_CODE
        setting_value.value = ""
        setting_value.save()

    if (
        setting_value.setting.is_translatable
        and lang != settings.LANGUAGE_CODE
    ):
        try:
            setting_value = setting_value.translations.get_language(lang)
        except ObjectDoesNotExist:
            setting_value = setting_value.translate(lang)

    if setting.types == 'json':
        value = json.dumps(value)

    if setting.types == 'boolean':
        value = 'on' if value else ''

    setting_value.value = value

    setting_value.save()

    return setting_value


def save_plugin_setting(plugin, setting_name, value, journal):
    setting = models.PluginSetting.objects.get(name=setting_name)
    lang = get_language() or settings.LANGUAGE_CODE
    lang = lang if setting.is_translatable else settings.LANGUAGE_CODE

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
    lang = get_language() or settings.LANGUAGE_CODE
    try:
        try:
            setting = models.PluginSetting.objects.get(name=setting_name, plugin=plugin)
        except models.PluginSetting.DoesNotExist:
            #Some Plugins rely on this function to install themselves
            logger.warning(
                "PluginSetting %s for plugin %s was not present, "
                "was the plugin installed correctly?"
                "" % (setting_name, plugin)
            )
            if create:
                setting, created = models.PluginSetting.objects.get_or_create(
                    name=setting_name,
                    plugin=plugin,
                    types=types,
                    defaults={'pretty_name': pretty, 'types': types}
                )

            if created:
                save_plugin_setting(plugin, setting_name, ' ', journal)

        lang = lang if setting.is_translatable else settings.LANGUAGE_CODE

        return _get_plugin_setting(plugin, setting, journal, lang, create, fallback)
    except Exception as e:
        logger.critical(
                "Failed to load plugin setting for context:\n"
                "plugin: {0},\n"
                "setting_name: {1},\n"
                "journal: {2},\n"
                "fallback: {3},\n"
                "request language: {4},\n"
                "settings language: {5},\n"
                "".format(
                    plugin, setting_name, journal,
                    fallback, lang, settings.LANGUAGE_CODE
                )
            )
        raise e


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
