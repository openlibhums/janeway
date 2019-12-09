# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models, connection, OperationalError


def populate_journal_is_secure(apps, schema_editor):
    Journal = apps.get_model("journal", "Journal")
    Setting = apps.get_model("core", "Setting")
    SettingValue = apps.get_model("core", "SettingValue")

    journals = Journal.objects.all()

    for journal in journals:

        value = None

        setting = Setting.objects.get(
            group__name='general',
            name='is_secure'
        )

        try:
            value = SettingValue.objects.get(
                setting=setting,
                journal=journal,
            )

            SQL = """
            SELECT * FROM core_settingvalue_translation
            WHERE master_id = {master_id}
            """.format(master_id=value.pk)

            with connection.cursor() as cursor:
                cursor.execute(SQL)
                value = cursor.fetchall()[0][1]

            if value == 'on':
                journal.is_secure = True
            else:
                journal.is_secure = False

            journal.save()
        except SettingValue.DoesNotExist:
            pass


class Migration(migrations.Migration):

    dependencies = [
        ('journal', '0019_journal_view_pdf_button'),
    ]

    operations = [
        migrations.AddField(
            model_name='journal',
            name='is_secure',
            field=models.BooleanField(default=False, help_text='If the site should redirect to HTTPS, mark this.'),
        ),
        migrations.RunPython(populate_journal_is_secure, reverse_code=migrations.RunPython.noop)
    ]
