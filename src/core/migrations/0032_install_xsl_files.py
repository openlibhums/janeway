# -*- coding: utf-8 -*-
import os
from django.db import migrations
from django.conf import settings
from django.core.files import File as DjangoFile


def install_xsl_files(apps, schema_editor):
    default_xsl_path = os.path.join(settings.BASE_DIR, "transform/xsl/default.xsl")
    install_xsl_file(
        apps,
        label=settings.DEFAULT_XSL_FILE_LABEL,
        path=default_xsl_path
    )


def install_xsl_file(apps, label, path=None, file_=None):
    XSLFile = apps.get_model('core', 'XSLFile')
    if XSLFile.objects.filter(label=label).exists():
        return
    xsl_file = XSLFile(label=label)
    if path:
        with open(path, 'r') as f:
            xsl_file.file = DjangoFile(f)
            xsl_file.save()
    elif file_:
        xsl_file = file_
        xsl_file.save()
    else:
        raise RuntimeError("No file or path provided for '%s'" % label)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0031_auto_20191103_2035'),
    ]

    operations = [
        migrations.RunPython(install_xsl_files, reverse_code=migrations.RunPython.noop),
    ]
