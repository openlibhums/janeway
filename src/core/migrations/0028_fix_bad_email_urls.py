# -*- coding: utf-8 -*-
from functools import partial
import re
from django.db import migrations

REGEX = re.compile("({{\ ?request.journal.site_url\ ?}}){% url '(\w+)' ([\w\ \.]*)%}")
OUTPUT_FMT = "{%% journal_url '%s' %s%%}"

def replace_matches( match):
    view_name = match.group(2)
    args = match.group(3)
    return OUTPUT_FMT % (view_name, args)

def replace_bad_urls(apps, schema_editor):
    SettingValueTranslation = apps.get_model('core', 'SettingValueTranslation')
    settings = SettingValueTranslation.objects.all()
    for setting in settings:
        setting.value = re.sub(REGEX, replace_matches, setting.value)
        setting.save()

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0027_account_preferred_timezone'),
    ]

    operations = [
        migrations.RunPython(replace_bad_urls, reverse_code=migrations.RunPython.noop),
    ]
