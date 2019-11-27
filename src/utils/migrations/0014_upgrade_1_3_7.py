# -*- coding: utf-8 -*-
from django.db import migrations
from django.utils import timezone

VERSION = "1.3.7"

def rollback(apps, schema_editor):
    version_model = apps.get_model("utils", "Version")
    latest_version = version_model.objects.get(number=VERSION, rollback=None)
    latest_version.rollback = timezone.now()
    latest_version.save()

def upgrade(apps, schema_editor):
    version_model = apps.get_model("utils", "Version")
    new_version = version_model.objects.create(number=VERSION)
    new_version.save()

class Migration(migrations.Migration):

    dependencies = [
        ('utils', '0013_upgrade_1_3_6'),
        ('core', '0033_set_default_xml_galley_xsl'),
    ]

    operations = [
        migrations.RunPython(upgrade, reverse_code=rollback),
    ]
