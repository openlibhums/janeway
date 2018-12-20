# -*- coding: utf-8 -*-
from django.db import migrations


def replace_journal_base_url(apps, schema_editor):
    SettingValueTranslation = apps.get_model('core', 'SettingValueTranslation')
    settings = SettingValueTranslation.objects.all()
    for setting in settings:
        s.value = s.value.replace("request.journal_base_url", "journal.site_url")
        s.save()

def reverse_code(apps, schema_editor):
    SettingValueTranslation = apps.get_model('core', 'SettingValueTranslation')
    settings = SettingValueTranslation.objects.all()
    for setting in settings:
        s.value = s.value.replace("journal.site_url", "request.replace_journal_base_url")
        s.save()

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0022_merge_20181219_1312'),
    ]

    operations = [
        migrations.RunPython(replace_journal_base_url, reverse_code=migrations.RunPython.noop),
    ]
