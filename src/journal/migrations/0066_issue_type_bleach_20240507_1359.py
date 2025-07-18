# Generated by Django 3.2.20 on 2024-05-07 12:59

import core.model_utils
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("journal", "0065_prepub_send_notifications"),
        ("journal", "0065_issue_type_null_to_string"),
    ]

    operations = [
        migrations.AlterField(
            model_name="issuetype",
            name="custom_plural",
            field=core.model_utils.JanewayBleachCharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name="issuetype",
            name="pretty_name",
            field=core.model_utils.JanewayBleachCharField(max_length=255),
        ),
    ]
