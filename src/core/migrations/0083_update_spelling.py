# -*- coding: utf-8 -*-
from django.db import migrations


DESCRIPTIONS_TO_FIX = {
    "default_review_visibility": "Sets Open, Single Anonymous or Double Anonymous as the default for the anonymity drop down when creating a review assignment.",
}
NAMES_TO_FIX = {
    "default_review_visibility": "Default Review Anonymity",
}


def replace_settings(apps, schema_editor):
    Setting = apps.get_model('core', 'Setting')
    SettingValue = apps.get_model('core', 'SettingValue')

    for setting_name, description in DESCRIPTIONS_TO_FIX.items():
        settings = Setting.objects.filter(
            name=setting_name,
        ).update(description=description)

    for setting_name, pretty_name in NAMES_TO_FIX.items():
        settings = Setting.objects.filter(
            name=setting_name,
        ).update(pretty_name=pretty_name)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0082_galley_file_not_nullable'),
        ('core', '0082_mark_safe_article_title'),
        ('core', '0082_galley_file_not_nullable'),
        ('core', '0082_auto_20230515_1706'),
    ]

    operations = [
        migrations.RunPython(replace_settings, reverse_code=migrations.RunPython.noop),
    ]
