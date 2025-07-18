# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2022-02-02 14:26
from __future__ import unicode_literals

from django.db import migrations
from django.conf import settings


def update_password_reset(apps, schema_editor):
    SettingValue = apps.get_model("core", "SettingValue")
    setting_values = SettingValue.objects.filter(
        setting__group__name="email",
        setting__name="password_reset",
    )
    # Loop over all SettingValues and update all of the value strings for each available language.
    for setting_value in setting_values:
        for language in settings.LANGUAGES:
            value_string = "value_{}".format(language[0])

            if setting_value and hasattr(setting_value, value_string):
                old_string = getattr(
                    setting_value,
                    value_string,
                )
                if old_string:
                    for replacement in (
                        (
                            "{{ core_reset_password_url }} br/><br/>",
                            "{{ core_reset_password_url }}",
                        ),
                    ):
                        old_string = old_string.replace(*replacement)

                    setattr(
                        setting_value,
                        value_string,
                        old_string,
                    )
                    setting_value.save()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0063_fix_review_accept_ack"),
    ]

    operations = [
        migrations.RunPython(
            update_password_reset,
            reverse_code=migrations.RunPython.noop,
        )
    ]
