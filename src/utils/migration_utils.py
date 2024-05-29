__copyright__ = "Copyright 2021 Birkbeck, University of London"
__author__ = "Martin Paul Eve, Mauro Sanchez & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django.conf import settings
from django.utils import translation


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
