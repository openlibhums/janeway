# -*- coding: utf-8 -*-
import re
from django.conf import settings
from django.db import migrations

REGEX = re.compile("{{\ ?([a-z\._-]*)article.title\ ?}}")
OUTPUT_FMT = "{{ %sarticle.safe_title }}"

def replace_matches( match):
    prefix = match.group(1)
    return OUTPUT_FMT % prefix

def replace_article_title(apps, schema_editor):
    SettingValue = apps.get_model('core', 'SettingValue')
    setting_values= SettingValue.objects.all()
    for setting in setting_values:
        for language in settings.LANGUAGES:
            value_string = 'value_{}'.format(language[0])
            if setting and getattr(setting, value_string, None):
                setattr(
                    setting, value_string,
                    re.sub(REGEX, replace_matches, getattr(setting, value_string))
                )
                setting.save()

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0081_alter_account_preferred_timezone'),
    ]

    operations = [
        migrations.RunPython(replace_article_title, reverse_code=migrations.RunPython.noop),
    ]
