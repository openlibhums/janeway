# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2019-02-06 18:16
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("journal", "0021_journal_enable_correspondence_authors"),
    ]

    operations = [
        migrations.AddField(
            model_name="journal",
            name="is_conference",
            field=models.BooleanField(default=False),
        ),
    ]
