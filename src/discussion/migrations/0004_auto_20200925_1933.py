# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2020-09-25 19:33
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("discussion", "0003_auto_20200821_1422"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="thread",
            options={"ordering": ("-last_updated", "pk")},
        ),
    ]
