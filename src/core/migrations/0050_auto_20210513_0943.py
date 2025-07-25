# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2021-05-13 09:43
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0049_modeltranslations_tidy"),
    ]

    operations = [
        migrations.AddField(
            model_name="editorialgroup",
            name="description_cy",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="editorialgroup",
            name="description_de",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="editorialgroup",
            name="description_en",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="editorialgroup",
            name="description_fr",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="editorialgroup",
            name="name_cy",
            field=models.CharField(max_length=500, null=True),
        ),
        migrations.AddField(
            model_name="editorialgroup",
            name="name_de",
            field=models.CharField(max_length=500, null=True),
        ),
        migrations.AddField(
            model_name="editorialgroup",
            name="name_en",
            field=models.CharField(max_length=500, null=True),
        ),
        migrations.AddField(
            model_name="editorialgroup",
            name="name_fr",
            field=models.CharField(max_length=500, null=True),
        ),
    ]
