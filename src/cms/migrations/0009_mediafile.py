# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2021-10-11 14:33
from __future__ import unicode_literals

import cms.models
import core.file_system
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("journal", "0046_auto_20210922_1436"),
        ("cms", "0008_auto_20210825_1432"),
    ]

    operations = [
        migrations.CreateModel(
            name="MediaFile",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("label", models.CharField(max_length=255)),
                (
                    "file",
                    models.FileField(
                        storage=core.file_system.JanewayFileSystemStorage(),
                        upload_to=cms.models.upload_to_media_files,
                    ),
                ),
                ("uploaded", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "journal",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="journal.Journal",
                    ),
                ),
            ],
        ),
    ]
