# -*- coding: utf-8 -*-
# Generated by Django 1.11.23 on 2020-01-17 12:40
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("copyediting", "0005_auto_20190523_1758"),
    ]

    operations = [
        migrations.AlterField(
            model_name="copyeditassignment",
            name="copyeditor_files",
            field=models.ManyToManyField(blank=True, to="core.File"),
        ),
    ]
