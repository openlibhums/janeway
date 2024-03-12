# -*- coding: utf-8 -*-
from django.db import migrations

SETTING_VALUES_TO_FIX = {
    "review_file_help": {
        "old": "<p>If you are undertaking a blind or double-blind review you must ensure that the file has any identifying text removed. Consider:</p> <ol> <li>If the paper has a title page removing the authors name and contact information.</li> <li>Check the bibliography and the text for self-citation</li> <li>Also check for mentions not made explicitly. The following phrases might give away an author&rsquo;s identity and should be edited:</li> <ul> <li>&lsquo;As I previously discussed&hellip;.&rsquo;</li> <li>&lsquo;As I have showed&hellip;&rsquo;</li> <li>&lsquo;My previous work&hellip;.&rsquo;</li> </ul> <li>Remove any identifying metadata from the file.</li> </ol>",
        "new": "<p>If you are undertaking a single anonymous or double anonymous review you must ensure that the file has any identifying text removed. Consider:</p> <ol> <li>If the paper has a title page removing the authors name and contact information.</li> <li>Check the bibliography and the text for self-citation</li> <li>Also check for mentions not made explicitly. The following phrases might give away an author&rsquo;s identity and should be edited:</li> <ul> <li>&lsquo;As I previously discussed&hellip;.&rsquo;</li> <li>&lsquo;As I have showed&hellip;&rsquo;</li> <li>&lsquo;My previous work&hellip;.&rsquo;</li> </ul> <li>Remove any identifying metadata from the file.</li> </ol>"
    },
    "peer_review_info": {
        "old": "This journal operates a open/blind/double blind peer review policy.",
        "new": "This journal operates a open/single anonymous/double anonymous, peer review policy.",
    },
}

DESCRIPTIONS_TO_FIX = {
    "review_file_help": "Text displayed when a journal defaults to single anonymous or double anonymous review ensuring that files remain anonymous.",
    "defaul_review_visibility": "Sets Open, Single Anonymous or Double Anonymous as the default for the anonimity drop down when creating a review assignment.",
}
NAMES_TO_FIX = {
    "defaul_review_visibility": "Default Review Anonimity",
}


def replace_settings(apps, schema_editor):
    Setting = apps.get_model('core', 'Setting')
    SettingValue = apps.get_model('core', 'SettingValue')
    for setting_name, values in SETTING_VALUES_TO_FIX.items():
        settings = SettingValue.objects.filter(
            setting__name=setting_name,
            value_en=values["old"]
        )
        settings.update(value_en=values["new"])

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
        ('core', '0077_merge_20221004_1031'),
    ]

    operations = [
        migrations.RunPython(replace_settings, reverse_code=migrations.RunPython.noop),
    ]
