# Generated by Django 4.2.14 on 2024-07-26 13:26

import core.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("submission", "0083_article_jats_article_type_override_and_more"),
        ("core", "0105_migrate_affiliation_institution"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="account",
            name="country",
        ),
        migrations.RemoveField(
            model_name="account",
            name="department",
        ),
        migrations.RemoveField(
            model_name="account",
            name="institution",
        ),
        migrations.RemoveField(
            model_name="organization",
            name="migration_id",
        ),
    ]
