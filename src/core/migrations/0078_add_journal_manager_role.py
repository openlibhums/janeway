# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

from utils import install
from core import models as core_models


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

    def install_permissions(apps, schema_editor):
        try:
            install.load_permissions()
        except core_models.Setting.DoesNotExist:
            # This data migration can be ignored on a first load,
            # permissions will be added during the load_default_settings
            # command. See utils/install.py for more information.
            pass

    dependencies = [
        ('core', '0077_merge_20221004_1031'),
    ]

    operations = [
        migrations.RunPython(add_role, reverse_code=remove_role),
        migrations.AddField(
            model_name='setting',
            name='editable_by',
            field=models.ManyToManyField(blank=True,
                                         help_text='Determines who can edit this setting based on their assigned roles.',
                                         to='core.Role'),
        ),
        migrations.RunPython(
            install_permissions,
            reverse_code=migrations.RunPython.noop,
        ),
    ]