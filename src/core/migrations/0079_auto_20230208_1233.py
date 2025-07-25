# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2023-02-08 12:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0078_anonymous_review_rewording"),
    ]

    operations = [
        migrations.AddField(
            model_name="contacts",
            name="name_en_us",
            field=models.CharField(max_length=300, null=True),
        ),
        migrations.AddField(
            model_name="contacts",
            name="role_en_us",
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.AddField(
            model_name="editorialgroup",
            name="description_en_us",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="editorialgroup",
            name="name_en_us",
            field=models.CharField(max_length=500, null=True),
        ),
        migrations.AddField(
            model_name="settingvalue",
            name="value_en_us",
            field=models.TextField(blank=True, null=True),
        ),
    ]
