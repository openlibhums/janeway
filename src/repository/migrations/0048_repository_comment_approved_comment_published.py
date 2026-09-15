import json
import os

from django.conf import settings
from django.db import migrations
import core.model_utils


def get_repository_settings():
    settings_path = os.path.join(
        settings.BASE_DIR,
        "utils/install/repository_settings.json",
    )
    with open(settings_path) as f:
        return json.load(f)[0]


def set_comment_email_defaults(apps, schema_editor):
    defaults = get_repository_settings()
    Repository = apps.get_model("repository", "Repository")
    Repository.objects.all().update(
        new_comment=defaults["new_comment"],
        comment_published=defaults["comment_published"],
        comment_approved=defaults["comment_approved"],
    )


class Migration(migrations.Migration):
    dependencies = [
        ("repository", "0047_remove_preprintauthor_affiliation_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="repository",
            name="comment_published",
            field=core.model_utils.JanewayBleachField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="historicalrepository",
            name="comment_published",
            field=core.model_utils.JanewayBleachField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="repository",
            name="comment_approved",
            field=core.model_utils.JanewayBleachField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="historicalrepository",
            name="comment_approved",
            field=core.model_utils.JanewayBleachField(blank=True, null=True),
        ),
        migrations.RunPython(
            set_comment_email_defaults,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
