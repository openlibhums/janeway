# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    def add_role(apps, schema_editor):
        Role = apps.get_model("core", "Role")
        role = Role(
            name='Journal Manager',
            slug='journal-manager',
        )
        role.save()

    def remove_role(apps, schema_editor):
        Role = apps.get_model("core", "Role")
        Role.objects.filter(
            slug='journal-manager',
        ).delete()

    dependencies = [
        ('core', '0077_merge_20221004_1031'),
    ]

    operations = [
        migrations.RunPython(add_role, reverse_code=remove_role),
    ]