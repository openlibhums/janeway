# Generated by Django 4.2 on 2024-06-05 09:24

from django.db import migrations

from utils import migration_utils

settings = [
    {
        "name": "notification_acceptance",
        "group_name": "email",
    },
    {
        "name": "subject_notification_acceptance",
        "group_name": "email_subject",
    },
]


def delete_notification_acceptance_setting(apps, schema_editor):
    for setting in settings:
        migration_utils.delete_setting(
            apps=apps,
            setting_group_name=setting.get("group_name"),
            setting_name=setting.get("name"),
        )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0095_merge_20240621_0722"),
    ]

    operations = [
        migrations.RunPython(
            delete_notification_acceptance_setting,
            reverse_code=migrations.RunPython.noop,
        )
    ]
