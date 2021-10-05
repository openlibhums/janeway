# -*- coding: utf-8 -*-

from django.db import migrations, models
from django.utils import timezone

VERSION = "1.4.0"

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
        ('utils', '0022_merge_20210624_0923'),
        ('core', '0057_xslt_1-4-0'),
    ]

    operations = [
        migrations.AlterField(
            model_name='version',
            name='number',
            field=models.CharField(max_length=10),
        ),
        migrations.RunPython(upgrade, reverse_code=rollback),
    ]
