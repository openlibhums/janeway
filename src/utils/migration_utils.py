__copyright__ = "Copyright 2021 Birkbeck, University of London"
__author__ = "Martin Paul Eve, Mauro Sanchez & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django.conf import settings
from django.apps import apps
from django.utils import translation


def update_translated_settings(setting_name, group_name, values_to_replace, replacement_value):
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

