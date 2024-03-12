# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.management import call_command
from django.db import migrations, models


def update_setting_values(apps, schema_editor):
    Journal = apps.get_model("journal", "Journal")
    Setting = apps.get_model("core", "Setting")
    SettingGroup = apps.get_model("core", "SettingGroup")
    SettingValue = apps.get_model("core", "SettingValue")
    setting_group, _ = SettingGroup.objects.get_or_create(
        name="article")
    call_command('load_default_settings')

    thumb_setting, c = Setting.objects.get_or_create(name="disable_article_thumbnails")
    large_image_setting = Setting.objects.get(name="disable_article_large_image")

    for journal in Journal.objects.filter(disable_article_images=True):
        SettingValue.objects.get_or_create(
            setting=thumb_setting,
            value_en="on",
            journal=journal,
        )
        SettingValue.objects.get_or_create(
            setting=large_image_setting,
            value_en="on",
            journal=journal,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('journal', '0052_add_fields_to_fixedpubcheckitems_and_issue'),
    ]

    operations = [
        migrations.RunPython(update_setting_values, reverse_code=migrations.RunPython.noop),
    ]
