# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2020-11-05 20:51
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("review", "0009_review_form_element_order"),
    ]

    operations = [
        migrations.AlterField(
            model_name="reviewassignmentanswer",
            name="answer",
            field=models.TextField(blank=True, null=True),
        ),
    ]
