# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2022-06-30 14:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0072_auto_20220623_1028"),
    ]

    operations = [
        migrations.AlterField(
            model_name="account",
            name="username",
            field=models.CharField(
                max_length=254, unique=True, verbose_name="Username"
            ),
        ),
    ]
