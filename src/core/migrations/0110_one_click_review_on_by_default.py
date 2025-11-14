# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def update_default_setting(apps, schema_editor):
    SettingValue = apps.get_model("core", "SettingValue")
    setting_values = SettingValue.objects.filter(
        setting__name="enable_one_click_access",
        journal__isnull=False,
    )
    setting_values.update(value="on")


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0109_auto_20250909_1421"),
    ]

    operations = [
        migrations.RunPython(
            update_default_setting,
            reverse_code=migrations.RunPython.noop,
        )
    ]
