# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-11-21 11:15
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("submission", "0017_auto_20171114_1502"),
        ("cron", "0002_auto_20170711_1203"),
    ]

    operations = [
        migrations.AddField(
            model_name="crontask",
            name="article",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="submission.Article",
            ),
        ),
        migrations.AlterField(
            model_name="reminder",
            name="template_name",
            field=models.CharField(
                help_text="The name of the email template, if it doesn't existyou will be asked to create it. Should have no spaces.",
                max_length=100,
            ),
        ),
    ]
