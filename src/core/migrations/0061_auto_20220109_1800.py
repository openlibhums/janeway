# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2022-01-09 18:00
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
    Setting.objects.filter(
        name__in=STYLING_SETTINGS,
        group__name=from_group,
    ).update(group=setting_group)


def general_to_styling(apps, schema_editor):
    update_settings_group(apps, STYLING_SETTINGS, "general", "styling")


def styling_to_general(apps, schema_editor):
    update_settings_group(apps, STYLING_SETTINGS, "styling", "general")


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0060_remove_display_about_on_submissions"),
    ]

    operations = [
        migrations.RunPython(general_to_styling, reverse_code=styling_to_general),
    ]
