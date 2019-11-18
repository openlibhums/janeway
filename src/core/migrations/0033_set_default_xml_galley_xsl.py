# -*- coding: utf-8 -*-
import os
from django.db import migrations
from django.conf import settings

def set_galley_xsl(apps, schema_editor):
    Galley = apps.get_model("core", "Galley")
    XSLFile = apps.get_model("core", "XSLFile")
    xsl_file = XSLFile.objects.get(label=settings.DEFAULT_XSL_FILE_LABEL)
    for galley in Galley.objects.filter(label='XML'):
        galley.xsl_file = xsl_file
        galley.save()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0032_install_xsl_files'),
    ]

    operations = [
        migrations.RunPython(set_galley_xsl, reverse_code=migrations.RunPython.noop),
    ]
