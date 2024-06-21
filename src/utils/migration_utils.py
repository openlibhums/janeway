__copyright__ = "Copyright 2021 Birkbeck, University of London"
__author__ = "Martin Paul Eve, Mauro Sanchez & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django.conf import settings
from django.utils import translation
from django.db.models import Q


def update_translated_settings(apps, setting_name, group_name, values_to_replace, replacement_value):
    """
    Gets a setting then iterates through available languages replacing a list of strings with a
    replacement string.
    """
    SettingValue = apps.get_model('core', 'SettingValue')
    languages = [lang[0] for lang in settings.LANGUAGES]

    setting_values = SettingValue.objects.filter(
        setting__name=setting_name,
        setting__group__name=group_name,
    )

    for setting_value in setting_values:
        for language in languages:

            with translation.override(language):
                value = setting_value.value

                if value:
                    for value_to_replace in values_to_replace:
                        value = value.replace(
                            value_to_replace,
                            replacement_value,
                        )
                    setting_value.value = value
                    setting_value.save()


def update_setting_types(
    model,
    group_name,
    old_type,
    new_type,
    setting_name=None,
):
    """
    Updates setting types based on setting group, current type,
    and optionally on setting name.
    """
    query = Q(group__name=group_name, types=old_type)
    if setting_name:
        query &= Q(name=setting_name)
    model.objects.filter(query).update(types=new_type)


def replace_strings_in_setting_values(
    apps,
    setting_name,
    group_name,
    replacements,
    languages=None,
):
    """
    Replaces a substring with a new substring in matching setting values.
    Accounts for translatable settings that use django-modeltranslation.
    :param setting_name: Setting.name
    :param group_name: SettingGroup.name
    :param replacements: A list of tuples containing old and new strings.
    :param languages: A list of language codes to check for old and new strings.
    """
    if not languages:
        languages = ['en']
    with translation.override('en'):
        SettingValue = apps.get_model('core', 'SettingValue')
        setting_values = SettingValue.objects.filter(
            setting__name=setting_name,
            setting__group__name=group_name,
        )

        for setting_value in setting_values:
            for language in languages:
                language_var = f'value_{language}'
                value = getattr(setting_value, language_var, '')
                if not value:
                    continue
                for old_string, new_string in replacements:
                    if old_string in value:
                        value = value.replace(old_string, new_string)
                        setattr(setting_value, language_var, value)
                        setting_value.save()
