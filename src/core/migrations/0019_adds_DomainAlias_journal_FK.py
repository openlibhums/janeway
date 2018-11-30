# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.sites.models import Site
from django.db import migrations, models
import django.db.models.deletion

def populate_domain_alias_journals(apps, schema_editor):
    DomainAlias = apps.get_model("core", "DomainAlias")
    Journal = apps.get_model("journal", "Journal")
    domain_aliases = DomainAlias.objects.all()
    for da in domain_aliases:
        site = Site.objects.get(id=da.site_id)
        journal = Journal.objects.get(domain=site.domain)
        da.journal = journal
        da.save()

class Migration(migrations.Migration):

    dependencies = [
        ('journal', '0017_file_fields_for_the_last_time'),
        ('core', '0018_auto_20181116_1123'),
    ]

    operations = [
        migrations.AddField(
            model_name='domainalias',
            name='journal',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='journal.Journal', null=True),
            preserve_default=False,
        ),
        migrations.RunPython(populate_domain_alias_journals)
    ]
