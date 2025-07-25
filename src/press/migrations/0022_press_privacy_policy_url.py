# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2020-11-23 12:51
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("press", "0021_auto_20190329_1202"),
    ]

    operations = [
        migrations.AddField(
            model_name="press",
            name="privacy_policy_url",
            field=models.URLField(
                blank=True,
                help_text="URL to an external privacy-policy, linked from the page footer. If blank, it links to the Janeway CMS page: /site/privacy.",
                max_length=999,
                null=True,
            ),
        ),
    ]
