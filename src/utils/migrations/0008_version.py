# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2018-08-08 15:07
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("utils", "0007_auto_20171215_1051"),
    ]

    operations = [
        migrations.CreateModel(
            name="Version",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("number", models.CharField(max_length=5)),
                ("date", models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
    ]
