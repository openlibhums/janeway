# -*- coding: utf-8 -*-
import os
from django.db import migrations
from django.conf import settings


def set_default_xsl(apps, schema_editor):
    Journal = apps.get_model("journal", "Journal")
    XSLFile = apps.get_model("core", "XSLFile")
    xsl_file = XSLFile.objects.get(label=settings.DEFAULT_XSL_FILE_LABEL)
    for journal in Journal.objects.all():
        journal.xsl = xsl_file
        journal.save()


class Migration(migrations.Migration):

    dependencies = [
        ('journal', '0035_journal_xsl'),
    ]

    operations = [
        migrations.RunPython(set_default_xsl, reverse_code=migrations.RunPython.noop),
    ]
