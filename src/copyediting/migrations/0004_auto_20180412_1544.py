# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2018-04-12 15:44
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("copyediting", "0003_auto_20180122_2211"),
    ]

    operations = [
        migrations.AlterField(
            model_name="copyeditassignment",
            name="decision",
            field=models.CharField(
                blank=True,
                choices=[
                    ("accept", "Accept"),
                    ("decline", "Decline"),
                    ("cancelled", "Cancelled"),
                ],
                max_length=20,
                null=True,
            ),
        ),
    ]
