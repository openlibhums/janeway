# -*- coding: utf-8 -*-
from django.db import migrations


OLD_VALUE = "Dear {{ review_assignment.reviewer.full_name }}, <br><br>Thank you for agreeing to review \"{{ article.title }}\" in {{ article.journal.name }}. <br><br>You can now access the manuscript and the review process at: <a href=\"{% journal_url 'do_review' review_assignment.id  %}\">{% journal_url 'do_review' review_assignment.id  %}</a>. <br><br>Regards, <br>{{ request.user.signature|safe }}"

NEW_VALUE = "Dear {{ review_assignment.reviewer.full_name }}, <br><br>Thank you for agreeing to review \"{{ article.title }}\" in {{ article.journal.name }}. <br><br>You can now access the manuscript and the review process at: <a href=\"{% journal_url 'do_review' review_assignment.id  %}\">{% journal_url 'do_review' review_assignment.id  %}</a>. <br><br>Regards, <br>{{ review_assignment.editor.signature|safe }}"


def replace_template(apps, schema_editor):
    SettingValueTranslation = apps.get_model('core', 'SettingValueTranslation')
    settings = SettingValueTranslation.objects.filter(value=OLD_VALUE)

    for setting in settings:
        setting.value = NEW_VALUE
        setting.save()

def reverse_code(apps, schema_editor):
    SettingValueTranslation = apps.get_model('core', 'SettingValueTranslation')
    settings = SettingValueTranslation.objects.filter(value=NEW_VALUE)
    for setting in settings:
        setting.value = OLD_VALUE
        setting.save()

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0033_set_default_xml_galley_xsl'),
    ]

    operations = [
        migrations.RunPython(replace_template, reverse_code=reverse_code),
    ]
