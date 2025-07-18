# Generated by Django 4.2.11 on 2024-04-30 17:04

from django.db import migrations
from utils.migration_utils import replace_strings_in_setting_values


HTML_ENTITIES_TO_FIX = [
    ("&amp;", "&"),
    ("&lt;", "<"),
    ("&gt;", ">"),
]


def repair_entities_in_journal_name(apps, schema_editor):
    replace_strings_in_setting_values(
        apps,
        "journal_name",
        "general",
        HTML_ENTITIES_TO_FIX,
        languages=["cy", "de", "en", "en-us", "en_us", "es", "fr", "it", "nl"],
    )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0090_setting_value"),
    ]

    operations = [
        migrations.RunPython(
            repair_entities_in_journal_name, reverse_code=migrations.RunPython.noop
        ),
    ]
