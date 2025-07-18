# -*- coding: utf-8 -*-
# Generated by Django 1.9.13 on 2017-07-11 12:03
from __future__ import unicode_literals

import django.core.files.storage
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import journal.models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ArticleOrdering",
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
                ("order", models.PositiveIntegerField(default=1)),
            ],
        ),
        migrations.CreateModel(
            name="BannedIPs",
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
                ("ip", models.GenericIPAddressField()),
                ("date_banned", models.DateField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="FixedPubCheckItems",
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
                ("metadata", models.BooleanField(default=False)),
                ("verify_doi", models.BooleanField(default=False)),
                ("select_issue", models.BooleanField(default=False)),
                ("set_pub_date", models.BooleanField(default=False)),
                ("notify_the_author", models.BooleanField(default=False)),
                ("select_render_galley", models.BooleanField(default=False)),
                ("select_article_image", models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name="Issue",
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
                ("volume", models.IntegerField(default=1)),
                ("issue", models.IntegerField(default=1)),
                ("issue_title", models.CharField(blank=True, max_length=300)),
                ("date", models.DateTimeField(default=django.utils.timezone.now)),
                ("order", models.IntegerField(default=1)),
                (
                    "issue_type",
                    models.CharField(
                        choices=[("Issue", "Issue"), ("Collection", "Collection")],
                        default="Issue",
                        max_length=200,
                    ),
                ),
                ("issue_description", models.TextField()),
                (
                    "cover_image",
                    models.ImageField(
                        blank=True,
                        null=True,
                        storage=django.core.files.storage.FileSystemStorage(
                            location="/home/ajrbyers/code/janeway/src/media"
                        ),
                        upload_to=journal.models.cover_images_upload_path,
                    ),
                ),
                (
                    "large_image",
                    models.ImageField(
                        blank=True,
                        null=True,
                        storage=django.core.files.storage.FileSystemStorage(
                            location="/home/ajrbyers/code/janeway/src/media"
                        ),
                        upload_to=journal.models.issue_large_image_path,
                    ),
                ),
            ],
            options={
                "ordering": ("order", "-date"),
            },
        ),
        migrations.CreateModel(
            name="Journal",
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
                ("code", models.CharField(max_length=4)),
                (
                    "domain",
                    models.CharField(default="localhost", max_length=255, unique=True),
                ),
                (
                    "default_cover_image",
                    models.ImageField(
                        blank=True,
                        null=True,
                        storage=django.core.files.storage.FileSystemStorage(
                            location="/home/ajrbyers/code/janeway/src/media"
                        ),
                        upload_to=journal.models.cover_images_upload_path,
                    ),
                ),
                (
                    "default_large_image",
                    models.ImageField(
                        blank=True,
                        null=True,
                        storage=django.core.files.storage.FileSystemStorage(
                            location="/home/ajrbyers/code/janeway/src/media"
                        ),
                        upload_to=journal.models.cover_images_upload_path,
                    ),
                ),
                (
                    "header_image",
                    models.ImageField(
                        blank=True,
                        null=True,
                        storage=django.core.files.storage.FileSystemStorage(
                            location="/home/ajrbyers/code/janeway/src/media"
                        ),
                        upload_to=journal.models.cover_images_upload_path,
                    ),
                ),
                (
                    "favicon",
                    models.ImageField(
                        blank=True,
                        null=True,
                        storage=django.core.files.storage.FileSystemStorage(
                            location="/home/ajrbyers/code/janeway/src/media"
                        ),
                        upload_to=journal.models.cover_images_upload_path,
                    ),
                ),
                (
                    "description",
                    models.TextField(
                        blank=True, null=True, verbose_name="Journal Description"
                    ),
                ),
                ("is_remote", models.BooleanField(default=False)),
                ("remote_submit_url", models.URLField(blank=True, null=True)),
                ("remote_view_url", models.URLField(blank=True, null=True)),
                ("nav_home", models.BooleanField(default=True)),
                ("nav_articles", models.BooleanField(default=True)),
                ("nav_issues", models.BooleanField(default=True)),
                ("nav_contact", models.BooleanField(default=True)),
                ("nav_start", models.BooleanField(default=True)),
                ("nav_review", models.BooleanField(default=True)),
                ("nav_sub", models.BooleanField(default=True)),
                ("has_xslt", models.BooleanField(default=False)),
                ("hide_from_press", models.BooleanField(default=False)),
                ("sequence", models.PositiveIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name="Notifications",
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
                ("domain", models.CharField(max_length=100)),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("submission", "Submission"),
                            ("acceptance", "Acceptance"),
                        ],
                        max_length=10,
                    ),
                ),
                ("active", models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name="PrePublicationChecklistItem",
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
                ("completed", models.BooleanField(default=False)),
                ("completed_on", models.DateTimeField(blank=True, null=True)),
                ("title", models.TextField()),
                ("text", models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name="PresetPublicationCheckItem",
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
                ("title", models.TextField()),
                ("text", models.TextField()),
                ("enabled", models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name="SectionOrdering",
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
                ("order", models.PositiveIntegerField(default=1)),
                (
                    "issue",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="journal.Issue"
                    ),
                ),
            ],
        ),
    ]
