# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2018-11-16 11:44
from __future__ import unicode_literals

import core.file_system
from django.db import migrations, models
import journal.models


class Migration(migrations.Migration):
    dependencies = [
        ("journal", "0016_journal_full_width_navbar"),
    ]

    operations = [
        migrations.AlterField(
            model_name="issue",
            name="cover_image",
            field=core.model_utils.SVGImageField(
                blank=True,
                help_text="Image representing the the cover of a printed issue or volume",
                null=True,
                storage=core.file_system.JanewayFileSystemStorage(),
                upload_to=journal.models.cover_images_upload_path,
            ),
        ),
        migrations.AlterField(
            model_name="issue",
            name="large_image",
            field=core.model_utils.SVGImageField(
                blank=True,
                help_text="landscape hero image used in the carousel and issue page",
                null=True,
                storage=core.file_system.JanewayFileSystemStorage(),
                upload_to=journal.models.issue_large_image_path,
            ),
        ),
        migrations.AlterField(
            model_name="journal",
            name="default_cover_image",
            field=core.model_utils.SVGImageField(
                blank=True,
                help_text="The default cover image for journal issues and for the journal's listing on the press-level website.",
                null=True,
                storage=core.file_system.JanewayFileSystemStorage(),
                upload_to=journal.models.cover_images_upload_path,
            ),
        ),
        migrations.AlterField(
            model_name="journal",
            name="default_large_image",
            field=core.model_utils.SVGImageField(
                blank=True,
                help_text="The default background image for article openers and carousel items.",
                null=True,
                storage=core.file_system.JanewayFileSystemStorage(),
                upload_to=journal.models.cover_images_upload_path,
            ),
        ),
        migrations.AlterField(
            model_name="journal",
            name="favicon",
            field=models.ImageField(
                blank=True,
                help_text="The tiny round or square image appearing in browser tabs before the webpage title",
                null=True,
                storage=core.file_system.JanewayFileSystemStorage(),
                upload_to=journal.models.cover_images_upload_path,
            ),
        ),
        migrations.AlterField(
            model_name="journal",
            name="header_image",
            field=core.model_utils.SVGImageField(
                blank=True,
                help_text="The logo-sized image at the top of all pages, typically used for journal logos.",
                null=True,
                storage=core.file_system.JanewayFileSystemStorage(),
                upload_to=journal.models.cover_images_upload_path,
            ),
        ),
    ]
