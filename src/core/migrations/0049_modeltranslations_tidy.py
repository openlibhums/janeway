# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2021-04-16 12:42
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0048_modeltranslations_data"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="settingvaluetranslation",
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name="settingvaluetranslation",
            name="master",
        ),
        migrations.AlterModelManagers(
            name="settingvalue",
            managers=[],
        ),
    ]
