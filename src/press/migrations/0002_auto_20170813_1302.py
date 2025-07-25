# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-08-13 13:02
from __future__ import unicode_literals

import django.core.files.storage
from django.db import migrations, models
import press.models


class Migration(migrations.Migration):
    dependencies = [
        ("press", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="press",
            name="default_carousel_image",
            field=models.ImageField(
                blank=True,
                null=True,
                storage=django.core.files.storage.FileSystemStorage(
                    location="/Users/ajrbyers/Code/janeway/src/media"
                ),
                upload_to=press.models.cover_images_upload_path,
            ),
        ),
        migrations.AlterField(
            model_name="press",
            name="favicon",
            field=models.ImageField(
                blank=True,
                null=True,
                storage=django.core.files.storage.FileSystemStorage(
                    location="/Users/ajrbyers/Code/janeway/src/media"
                ),
                upload_to=press.models.cover_images_upload_path,
            ),
        ),
    ]
