# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-10-13 08:50
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("press", "0009_press_preprint_editors"),
    ]

    operations = [
        migrations.CreateModel(
            name="PressSetting",
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
                ("name", models.CharField(max_length=255)),
                ("value", models.TextField(blank=True, null=True)),
                (
                    "press",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="press.Press"
                    ),
                ),
            ],
        ),
    ]
