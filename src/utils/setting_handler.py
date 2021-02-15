__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import json
import os
import codecs

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import get_language, activate

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
        default=True,
):
    """ Returns a matching SettingValue for the language in context

    It no journal is passed it returns the default setting directly. If
    default s True, it will attempt to return the default value respectively
    (in that order)
    :setting_group: (str) The group__name of the Setting
    :setting_name: (str) The name of the Setting
    :journal: (Journal object) The journal for which this setting is relevant.
        If None, returns the default value
    :create: If True, a journal override will be created if one is not present
    :default: If True, returns the default SettingValue when no journal specific
        value is present
    """
    setting = core_models.Setting.objects.get(name=setting_name)
    lang = get_language() if setting.is_translatable else settings.LANGUAGE_CODE
    try:
        return _get_setting(
            setting_group, setting, journal, lang, create, default)
    except Exception as e:
        logger.critical(
                "Failed to load setting for context:\n"
                "setting_name: {0},\n"
                "journal: {1},\n"
                "request language: {2},\n"
                "settings language: {3},\n"
                "".format(
                    setting_name, journal,
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
        default=True,
):

    try:
        setting_value_object = core_models.SettingValue.objects \
            .language(lang) \
            .get(
                setting__group__name=setting_group,
                setting=setting,
                journal=journal,
        )
        #  We call setting_value_object to force parler to check the active translation.
        setting_value_object.value
        return setting_value_object
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
                        lang, create,
                )
            else:
                return None
        else:
            raise


def save_setting(setting_group, setting_name, journal, value):
    setting = core_models.Setting.objects.get(
        name=setting_name,
        group__name=setting_group,
    )
    lang = get_language() if setting.is_translatable else settings.LANGUAGE_CODE

    if setting.types == 'json':
        value = json.dumps(value)

    if setting.types == 'boolean':
        value = 'on' if value else ''

    setting_value, created = core_models.SettingValue.objects.language(
        lang,
    ).get_or_create(
        setting=setting,
        journal=journal,
        defaults={
            'value': value,
        }
    )

    if not created:
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


def get_plugin_setting(plugin, setting_name, journal, create=False, pretty='', types='Text'):
    lang = get_language() or settings.LANGUAGE_CODE
    activate(lang)
    try:
        try:
            setting = models.PluginSetting.objects.get(name=setting_name, plugin=plugin)
            lang = lang if setting.is_translatable else settings.LANGUAGE_CODE
            return _get_plugin_setting(plugin, setting, journal, lang, create)
        except models.PluginSetting.DoesNotExist:
            # Some Plugins rely on this function to install themselves
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
                return _get_plugin_setting(plugin, setting, journal, lang, create)
            else:
                raise

    except Exception as e:
        logger.critical(
                "Failed to load plugin setting for context:\n"
                "plugin: {0},\n"
                "setting_name: {1},\n"
                "journal: {2},\n"
                "request language: {3},\n"
                "settings language: {4},\n"
                "".format(
                    plugin, setting_name, journal, lang, settings.LANGUAGE_CODE
                )
            )
        raise e


def _get_plugin_setting(plugin, setting, journal, lang, create):
    try:
        setting = models.PluginSettingValue.objects.get(
            setting__plugin=plugin,
            setting=setting,
            journal=journal,
        )
        return setting
    except models.PluginSettingValue.DoesNotExist:
        if create:
            return save_plugin_setting(plugin, setting.name, '', journal)
        else:
            raise IndexError('Plugin setting does not exist and will not be created.')


def get_email_subject_setting(setting_group, setting_name, journal, create=False):
    try:
        setting = core_models.Setting.objects.get(name=setting_name)
        lang = get_language() if setting.is_translatable else 'en'

        return _get_setting(setting_group, setting, journal, lang, create).value
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
