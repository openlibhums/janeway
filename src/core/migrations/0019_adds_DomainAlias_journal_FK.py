# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models, connection, utils
import django.db.models.deletion


JOURNAL_SITESECTOMY = """
    UPDATE core_domainalias SET journal_id = (
        SELECT j.id
            FROM journal_journal as j, django_site as s
            WHERE s.id = core_domainalias.site_id
            AND s.domain = j.domain
        );
"""

PRESS_SITESECTOMY = """
    UPDATE core_domainalias SET press_id = (
        SELECT p.id
            FROM press_press as p, django_site as s
            WHERE s.id = core_domainalias.site_id
            AND s.domain = p.domain
        );
"""


def sitesectomy(*args, **kwargs):
    with connection.cursor() as cursor:
        try:
            cursor.execute(JOURNAL_SITESECTOMY)
            cursor.execute(PRESS_SITESECTOMY)
        except utils.OperationalError:
            # New installations won't have a django_sites table
            pass

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
        migrations.RunPython(sitesectomy, reverse_code=migrations.RunPython.noop),
#        migrations.RunSQL(JOURNAL_SITESECTOMY, reverse_sql=migrations.RunSQL.noop),
#        migrations.RunSQL(PRESS_SITESECTOMY, reverse_sql=migrations.RunSQL.noop),
    ]
