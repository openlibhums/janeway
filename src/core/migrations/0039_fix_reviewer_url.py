# -*- coding: utf-8 -*-
# Generated by Django 1.11.28 on 2020-05-15 15:52
from __future__ import unicode_literals
import re

from django.db import migrations

REGEX = re.compile("({%\ ?journal_url 'do_review' review_assignment.id\ ?%})")
OUTPUT = "{{ review_url }}"


def replace_template(apps, schema_editor):
    SettingValueTranslation = apps.get_model("core", "SettingValueTranslation")
    settings = SettingValueTranslation.objects.all()

    for setting in settings:
        if isinstance(setting.value, str):
            setting.value = re.sub(REGEX, OUTPUT, setting.value)
            setting.save()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0038_xslt_1-3-8"),
    ]

    operations = [
        migrations.RunPython(replace_template, reverse_code=migrations.RunPython.noop)
    ]
