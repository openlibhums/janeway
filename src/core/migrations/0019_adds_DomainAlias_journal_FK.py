# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion

def populate_domain_alias_journals(apps, schema_editor):
    DomainAlias = apps.get_model("core", "DomainAlias")
    Journal = apps.get_model("journal", "Journal")
    Press = apps.get_model("press", "Press")
    Site = apps.get_model("sites", "Site")
    domain_aliases = DomainAlias.objects.all()
    for da in domain_aliases:
        site = Site.objects.get(id=da.site_id)
        try:
            da.journal = Journal.objects.get(domain=site.domain)
        except Journal.DoesNotExist:
            da.press = Press.objects.get(domain=site.domain)
        da.save()

class Migration(migrations.Migration):

    dependencies = [
        ('journal', '0017_file_fields_for_the_last_time'),
        ('core', '0018_auto_20181116_1123'),
    ]

    operations = [
        migrations.AddField(
            model_name='domainalias',
            name='press',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE, to='press.Press'),
        ),
        migrations.AlterField(
            model_name='domainalias',
            name='domain',
            field=models.CharField(default='www.example.com', max_length=255, unique=True),
        ),
        migrations.AddField(
            model_name='domainalias',
            name='journal',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE, to='journal.Journal'),
        ),
        migrations.RunPython(populate_domain_alias_journals, reverse_code=migrations.RunPython.noop)
    ]
