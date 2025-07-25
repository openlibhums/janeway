# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2021-05-10 11:48
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("cms", "0002_migrate_issue_types"),
    ]

    operations = [
        migrations.AddField(
            model_name="navigationitem",
            name="link_name_cy",
            field=models.CharField(
                help_text="The text that will appear in the nav bar (e.g. “About” or “Research Integrity”)",
                max_length=100,
                null=True,
                verbose_name="Display name",
            ),
        ),
        migrations.AddField(
            model_name="navigationitem",
            name="link_name_de",
            field=models.CharField(
                help_text="The text that will appear in the nav bar (e.g. “About” or “Research Integrity”)",
                max_length=100,
                null=True,
                verbose_name="Display name",
            ),
        ),
        migrations.AddField(
            model_name="navigationitem",
            name="link_name_en",
            field=models.CharField(
                help_text="The text that will appear in the nav bar (e.g. “About” or “Research Integrity”)",
                max_length=100,
                null=True,
                verbose_name="Display name",
            ),
        ),
        migrations.AddField(
            model_name="navigationitem",
            name="link_name_fr",
            field=models.CharField(
                help_text="The text that will appear in the nav bar (e.g. “About” or “Research Integrity”)",
                max_length=100,
                null=True,
                verbose_name="Display name",
            ),
        ),
        migrations.AddField(
            model_name="page",
            name="content_cy",
            field=models.TextField(
                blank=True,
                help_text="The content of the page. For headings, we recommend using the Style dropdown (looks like a wand) and selecting a heading level from 2 to 6, as the display name field occupies the place of heading level 1. Note that copying and pasting from a word processor can produce unwanted results, but you can use Remove Font Style (looks like an eraser) to remove some unwanted formatting. To edit the page as HTML, turn on the Code View (<>).",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="page",
            name="content_de",
            field=models.TextField(
                blank=True,
                help_text="The content of the page. For headings, we recommend using the Style dropdown (looks like a wand) and selecting a heading level from 2 to 6, as the display name field occupies the place of heading level 1. Note that copying and pasting from a word processor can produce unwanted results, but you can use Remove Font Style (looks like an eraser) to remove some unwanted formatting. To edit the page as HTML, turn on the Code View (<>).",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="page",
            name="content_en",
            field=models.TextField(
                blank=True,
                help_text="The content of the page. For headings, we recommend using the Style dropdown (looks like a wand) and selecting a heading level from 2 to 6, as the display name field occupies the place of heading level 1. Note that copying and pasting from a word processor can produce unwanted results, but you can use Remove Font Style (looks like an eraser) to remove some unwanted formatting. To edit the page as HTML, turn on the Code View (<>).",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="page",
            name="content_fr",
            field=models.TextField(
                blank=True,
                help_text="The content of the page. For headings, we recommend using the Style dropdown (looks like a wand) and selecting a heading level from 2 to 6, as the display name field occupies the place of heading level 1. Note that copying and pasting from a word processor can produce unwanted results, but you can use Remove Font Style (looks like an eraser) to remove some unwanted formatting. To edit the page as HTML, turn on the Code View (<>).",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="page",
            name="display_name_cy",
            field=models.CharField(
                help_text="Name of the page, in 100 characters or fewer, displayed in the nav and in the top-level heading on the page (e.g. “Research Integrity”).",
                max_length=100,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="page",
            name="display_name_de",
            field=models.CharField(
                help_text="Name of the page, in 100 characters or fewer, displayed in the nav and in the top-level heading on the page (e.g. “Research Integrity”).",
                max_length=100,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="page",
            name="display_name_en",
            field=models.CharField(
                help_text="Name of the page, in 100 characters or fewer, displayed in the nav and in the top-level heading on the page (e.g. “Research Integrity”).",
                max_length=100,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="page",
            name="display_name_fr",
            field=models.CharField(
                help_text="Name of the page, in 100 characters or fewer, displayed in the nav and in the top-level heading on the page (e.g. “Research Integrity”).",
                max_length=100,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="page",
            name="name",
            field=models.CharField(
                help_text="The relative URL path to the page, using lowercase letters and hyphens. For example, a page about research integrity might be “research-integrity”.",
                max_length=300,
                verbose_name="Link",
            ),
        ),
    ]
