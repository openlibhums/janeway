# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2020-12-21 13:59
from __future__ import unicode_literals

from django.db import migrations


def delete_settings(apps, schema_editor):
    Setting = apps.get_model("core", "Setting")
    Setting.objects.filter(
        group__name="email",
        name="review_request_sent",
    ).delete()


def update_setting_values(apps, schema_editor):
    SettingValueTranslation = apps.get_model("core", "SettingValueTranslation")

    prod_complete_settings = SettingValueTranslation.objects.filter(
        master__setting__name="production_complete",
        master__setting__group__name="email",
    )

    for setting in prod_complete_settings:
        setting.value = setting.value.replace(
            "<p>This article is now in the Proofing workflow: {{ proofing_list_url }}.</p>",
            "",
        )
        setting.value = setting.value.replace(
            "Dear {{ assignment.editor.full_name }},</p><p>This is an automatic",
            "This is a",
        )
        setting.save()

    typesetter_notification_settings = SettingValueTranslation.objects.filter(
        master__setting__name="typesetter_notification",
        master__setting__group__name="email",
    )

    for setting in typesetter_notification_settings:
        setting.value = setting.value.replace(
            "This is an automatic",
            "This is a",
        )
        setting.save()

    notify_editor_proofing_complete_settings = SettingValueTranslation.objects.filter(
        master__setting__name="notify_editor_proofing_complete",
        master__setting__group__name="email",
    )

    for setting in notify_editor_proofing_complete_settings:
        setting.value = setting.value.replace(
            ": {{ publish_url }}",
            "",
        )
        setting.save()

    review_ack_settings = SettingValueTranslation.objects.filter(
        master__setting__name="review_complete_reviewer_acknowledgement",
        master__setting__group__name="email",
    )

    for setting in review_ack_settings:
        setting.value = setting.value.replace(
            "request.user.signature",
            "review_assignment.editor.signature",
        )
        setting.save()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0045_fix_url_emails"),
    ]

    operations = [
        migrations.RunPython(
            delete_settings,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.RunPython(
            update_setting_values,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
