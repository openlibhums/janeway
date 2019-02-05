# -*- coding: utf-8 -*-
from functools import partial
import re
from django.db import migrations

REGEX = re.compile("({{\ ?journal.site_url\ ?}})?{% url '(\w+)' ([\w\ \.]*)%}")
OUTPUT_FMT = "{%% journal_url '%s' %s%%}"

def replace_matches( match):
    view_name = match.group(1)
    args = match.group(2)
    return OUTPUT_FMT % (view_name, args)

def replace_bad_urls(apps, schema_editor):
    SettingValueTranslation = apps.get_model('core', 'SettingValueTranslation')
    settings = SettingValueTranslation.objects.all()
    for setting in settings:
        setting.value = re.sub(REGEX, replace_matches, setting.value)
        setting.save()

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0024_auto_20190201_1015'),
    ]

    operations = [
        migrations.RunPython(replace_bad_urls, reverse_code=migrations.RunPython.noop),
    ]
