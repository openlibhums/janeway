"""
Migration that addresses the problem reported in GH#3006
On core.migrations.0061, a couple of settings got switched from the general
group to the styling group. The codebase was also change to lookup the settings
using the styling group.
However, the journal_defaults.json was never changed, which has lead to 2
possible wrong states.

Case A: pre-existing installation ran migration core.0061:
    - In this state the settings where swapped correctly to styling. however, 
      due to the setting group not being updated, a duplicate setting with the
      group general was re-introduced. This setting will not have any relevant
      values attached, since the codebase has been using the correct setting
      since
    - Action: Delete the setting associated with the general group
Case B: New installations since core.0061 was introduced:
    - In this state, migration 0061 would have run before the journal_defaults
      would've have been loaded. As a result, the styling group exists but
      the settings have always been on the general group. It is safe to delete
      these settings, because the codebase would have never allowed their values
      to be changed.
    - Action: Swap the group setting of the existing setting
      (essentially run 0061 again)

"""
from __future__ import unicode_literals

from django.db import migrations, models


STYLING_SETTINGS = [
    "enable_editorial_images",
    "multi_page_editorial",
]


def update_settings_group(apps, setting_names, from_group, to_group):
    Setting = apps.get_model("core", "Setting")
    SettingGroup = apps.get_model("core", "SettingGroup")
    setting_group, _ = SettingGroup.objects.get_or_create(name=to_group)
    for setting_name in STYLING_SETTINGS:
        settings = Setting.objects.filter(
            name=setting_name,
        )
        settings_with_from = settings.filter(group__name=from_group)
        settings_with_to = settings.filter(group__name=to_group)
        if settings_with_from.exists() and settings_with_to.exists():
            # Case A
            settings_with_from.delete()
        elif settings_with_from.exists() and not settings_with_to.exists():
            # Case B
            setting = settings_with_from.first()
            setting.group = setting_group
            setting.save()
            settings_with_from.delete()


def general_to_styling(apps, schema_editor):
    update_settings_group(apps, STYLING_SETTINGS, "general", "styling")


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0073_auto_20220630_1608'),
    ]

    operations = [
        migrations.RunPython(
            general_to_styling, reverse_code=migrations.RunPython.noop),
    ]
