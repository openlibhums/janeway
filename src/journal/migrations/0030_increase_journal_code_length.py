# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-05-23 15:02
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("journal", "0029_journal_code_unique"),
    ]

    operations = [
        migrations.AlterField(
            model_name="journal",
            name="code",
            field=models.CharField(max_length=15, unique=True),
        ),
    ]
