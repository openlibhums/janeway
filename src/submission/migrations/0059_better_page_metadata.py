# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2021-09-08 11:20
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.manager
import submission.models


class Migration(migrations.Migration):
    dependencies = [
        ("submission", "0058_merge_20210827_0849"),
    ]

    operations = [
        migrations.AlterModelManagers(
            name="article",
            managers=[
                ("allarticles", django.db.models.manager.Manager()),
                ("objects", submission.models.ArticleManager()),
            ],
        ),
        migrations.AddField(
            model_name="article",
            name="article_number",
            field=models.PositiveIntegerField(
                blank=True,
                help_text="Optional article number to be displayed on issue and article pages. Not to be confused with article ID.",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="article",
            name="first_page",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="article",
            name="last_page",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="article",
            name="publisher_name",
            field=models.CharField(
                blank=True,
                help_text="Name of the publisher who published this article Only relevant to migrated articles from a different publisher",
                max_length=999,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="article",
            name="rights",
            field=models.TextField(
                blank=True,
                help_text="A custom statement on the usage rights for this article and associated materials, to be rendered in the article page",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="article",
            name="total_pages",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="article",
            name="page_numbers",
            field=models.CharField(
                blank=True,
                help_text="Custom page range. e.g.: 'I-VII' or 1-3,4-8",
                max_length=32,
                null=True,
            ),
        ),
    ]
