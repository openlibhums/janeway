# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2020-11-02 10:04
from __future__ import unicode_literals

from django.db import migrations


def update_version_queues(apps, schema_editor):
    VersionQueue = apps.get_model("repository", "VersionQueue")

    for queue in VersionQueue.objects.all():
        queue.title = queue.preprint.title
        queue.abstract = queue.preprint.abstract
        queue.save()


class Migration(migrations.Migration):
    dependencies = [
        ("repository", "0019_auto_20201030_1423"),
    ]

    operations = [
        migrations.RunPython(
            update_version_queues,
            reverse_code=migrations.RunPython.noop,
        )
    ]
