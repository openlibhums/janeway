# -*- coding: utf-8 -*-
# Generated by Django 1.11.23 on 2020-02-10 14:12
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("typesetting", "0003_typesettingassignment"),
    ]

    operations = [
        migrations.AlterField(
            model_name="typesettingassignment",
            name="round",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                to="typesetting.TypesettingRound",
            ),
        ),
    ]
