# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-08-21 13:59
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("submission", "0002_auto_20170813_1302"),
    ]

    operations = [
        migrations.CreateModel(
            name="Field",
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
                ("name", models.CharField(max_length=200)),
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("text", "Text Field"),
                            ("textarea", "Text Area"),
                            ("check", "Check Box"),
                            ("select", "Select"),
                            ("email", "Email"),
                            ("date", "Date"),
                        ],
                        max_length=50,
                    ),
                ),
                (
                    "choices",
                    models.CharField(
                        blank=True,
                        help_text="Separate choices with the bar | character.",
                        max_length=1000,
                        null=True,
                    ),
                ),
                ("required", models.BooleanField(default=True)),
                ("order", models.IntegerField()),
                ("help_text", models.TextField()),
            ],
        ),
    ]
