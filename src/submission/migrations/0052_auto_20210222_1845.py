# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2021-02-22 18:45
from __future__ import unicode_literals

from django.db import migrations


def migrate_sections(apps, schema_editor):
    Section = apps.get_model("submission", "Section")
    SectionTranslation = apps.get_model("submission", "SectionTranslation")

    translations = SectionTranslation.objects.all()

    for translation in translations:
        section = Section.objects.get(pk=translation.master_id)
        setattr(
            section, "name_{}".format(translation.language_code), translation.hvad_name
        )
        setattr(
            section,
            "plural_{}".format(translation.language_code),
            translation.hvad_plural,
        )
        section.save()


class Migration(migrations.Migration):
    dependencies = [
        ("submission", "0051_hvad_to_modeltranslations"),
    ]

    operations = [
        migrations.RunPython(migrate_sections, reverse_code=migrations.RunPython.noop),
    ]
