# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2018-02-07 15:25
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0012_workflowlog"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="account",
            options={"ordering": ("first_name", "last_name", "username")},
        ),
        migrations.AlterModelOptions(
            name="workflowlog",
            options={"ordering": ("timestamp",)},
        ),
        migrations.AddField(
            model_name="workflowelement",
            name="article_url",
            field=models.BooleanField(default=True),
        ),
    ]
