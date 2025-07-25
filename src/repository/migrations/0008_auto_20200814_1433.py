# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2020-08-14 14:33
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0040_auto_20200529_1415"),
        ("repository", "0007_auto_20200813_1156"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="preprintaccess",
            name="location",
        ),
        migrations.AddField(
            model_name="preprintaccess",
            name="country",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="core.Country",
            ),
        ),
        migrations.AddField(
            model_name="preprintaccess",
            name="identifier",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="preprint",
            name="subject",
            field=models.ManyToManyField(null=True, to="repository.Subject"),
        ),
    ]
