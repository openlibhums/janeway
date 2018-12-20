# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

from journal.models import Journal

def populate_journal_is_secure(apps, schema_editor):
    journals = Journal.objects.all()
    for journal in journals:
        journal.is_secure = bool(journal.get_setting("general", "is_secure"))
        journal.save()

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
