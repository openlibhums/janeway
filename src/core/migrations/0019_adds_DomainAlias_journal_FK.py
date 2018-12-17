# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


JOURNAL_SITESECTOMY = """
    UPDATE core_domainalias da SET journal_id = (
        SELECT j.id
            FROM journal_journal j, django_site s
            WHERE s.id = da.site_id
            AND s.domain = j.domain
        );
"""

PRESS_SITESECTOMY = """
    UPDATE core_domainalias da SET press_id = (
        SELECT p.id
            FROM press_press p, django_site s
            WHERE s.id = da.site_id
            AND s.domain = p.domain
        );
"""


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
        migrations.RunSQL(JOURNAL_SITESECTOMY, reverse_sql=migrations.RunSQL.noop),
        migrations.RunSQL(PRESS_SITESECTOMY, reverse_sql=migrations.RunSQL.noop),
    ]
