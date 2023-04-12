# -*- coding: utf-8 -*-

from django.db import migrations, models
from django.utils import timezone

VERSION = "1.5.0"

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
        ('utils', '0029_alter_toaddress_options'),
        ('core', '0080_merge_20230317_1530'),
    ]

    operations = [
        migrations.RunPython(upgrade, reverse_code=rollback),
    ]
