__copyright__ = "Copyright 2021 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"


from django.conf import settings
from django.utils import translation
from django.db.models import Q


def update_translated_settings(apps, setting_name, group_name, values_to_replace, replacement_value):
    """
    Deprecated in 1.6, because it only works with an older translation
    setup that Janeway used to have.
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


def update_default_setting_values(apps, setting_name, group_name, values_to_replace, replacement_value):
    """
    Updates the specified default setting value where it has not been edited.
    Accounts for translatable settings that use django-modeltranslation.
    """
    with translation.override('en'):
        SettingValue = apps.get_model('core', 'SettingValue')
        setting_value = SettingValue.objects.filter(
            setting__name=setting_name,
            setting__group__name=group_name,
            journal=None,
        ).first()

        if setting_value:
            language_var = "value_{}".format('en')
            setattr(setting_value, language_var, replacement_value)
            setting_value.save()

            variants_to_delete = SettingValue.objects.filter(
                setting__name=setting_name,
                setting__group__name=group_name,
                journal__isnull=False,
            )

            for variant in variants_to_delete:
                if getattr(variant, language_var) in values_to_replace:
                    variant.delete()


def delete_setting(apps, setting_group_name, setting_name):
    """
    Used to delete a setting in migrations.
    """
    Setting = apps.get_model('core', 'Setting')
    setting = Setting.objects.filter(
        group__name=setting_group_name,
        name=setting_name,
    )
    setting.delete()


def store_empty_strings(model, fields):
    """
    A helper for preparing to remove null=True
    from string-based fields like CharField,
    where blank=True is also set.
    Sets all null values in the specified fields to empty strings.
    :param model: The model class produced from apps.get_model()
    :param fields: A list of fields that were null=True and are soon to be
    null=False
    """
    for field in fields:
        query = Q((f'{field}__isnull', True))
        model.objects.filter(query).update(**{field: ''})
