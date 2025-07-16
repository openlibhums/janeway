# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import re

from django.db import migrations

from metrics.logic import get_iso_country_code


def process_accesses(apps, schema_editor):
    ArticleAccess = apps.get_model("metrics", "ArticleAccess")
    Country = apps.get_model("core", "Country")

    accesses = ArticleAccess.objects.all()

    for access in accesses:
        check = re.match(
            r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$",
            access.identifier,
        )

        if check:
            try:
                code = get_iso_country_code(access.identifier)
                country = Country.objects.get(code=code)
            except Country.DoesNotExist:
                country = None

            access.country = country
            access.save()


class Migration(migrations.Migration):
    dependencies = [
        ("metrics", "0005_articleaccess_country"),
    ]

    operations = [
        migrations.RunPython(process_accesses, reverse_code=migrations.RunPython.noop)
    ]
