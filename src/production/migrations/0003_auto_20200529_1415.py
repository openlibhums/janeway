# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2020-05-29 14:15
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("production", "0002_typesettask_due"),
    ]

    operations = [
        migrations.AlterField(
            model_name="typesettask",
            name="galleys_loaded",
            field=models.ManyToManyField(
                blank=True, related_name="galleys_loaded", to="core.File"
            ),
        ),
    ]
