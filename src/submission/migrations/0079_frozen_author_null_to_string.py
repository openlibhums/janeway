from django.db import migrations

from utils import migration_utils


def migrate_null_values(apps, schema_editor):
    model = apps.get_model('submission', 'FrozenAuthor')
    fields = [
        'department',
        'first_name',
        'frozen_biography',
        'frozen_email',
        'frozen_orcid',
        'institution',
        'last_name',
        'middle_name',
        'name_prefix',
        'name_suffix',
    ]
    migration_utils.store_empty_strings(model, fields)


class Migration(migrations.Migration):

    dependencies = [
        ('submission', '0078_merge_0075_auto_20240312_0922_0077_auto_20240402_1326'),
    ]

    operations = [
        migrations.RunPython(
            migrate_null_values,
            reverse_code=migrations.RunPython.noop
        ),
    ]
