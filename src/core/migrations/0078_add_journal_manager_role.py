# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    def add_role(apps, schema_editor):
        Role = apps.get_model("core", "Role")
        new_role = Role.objects.create(
            name='Journal Manager',
            slug='journal-manager',
        )

    def remove_role(apps, schema_editor):
        Role = apps.get_model("core", "Role")
        new_role = Role.objects.filter(
            name='Journal Manager',
            slug='journal-manager',
        ).delete()

    dependencies = [
        ('core', '0077_merge_20221004_1031'),
    ]

    operations = [
        migrations.RunPython(add_role, remove_role),
    ]