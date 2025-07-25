# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2020-05-19 16:13
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("submission", "0042_auto_20200423_1534"),
    ]

    operations = [
        migrations.AddField(
            model_name="article",
            name="custom_how_to_cite",
            field=models.TextField(
                blank=True,
                help_text="Custom 'how to cite' text. To be used only if the block generated by Janeway is not suitable.",
                null=True,
            ),
        ),
    ]
