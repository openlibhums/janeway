# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2021-11-19 10:15
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("utils", "0023_upgrade_1_4_0"),
    ]

    operations = [
        migrations.AddField(
            model_name="logentry",
            name="email_subject",
            field=models.TextField(blank=True, null=True),
        ),
    ]
