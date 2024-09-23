from django.db import migrations
from utils import migration_utils


def update_typesetting_guide(apps, schema_editor):
    values_to_replace = [
        'Here are some guidelines.',
    ]

    replacement_value = '<p>When uploading galleys, please label them by the format, such as “XML” or “PDF”.</p><p>XML and HTML galleys can be previewed after uploading to check how they will be rendered when published.</p><p>The Galleys section should only contain one representative file for each format. If you are uploading the first version of a new format, please upload a new Galley (typeset file). If you are making revisions or corrections to an existing format, please use select <strong>Edit</strong> and then upload the new version, rather than adding a new Galley.</p>'

    migration_utils.update_default_setting_values(
        apps,
        setting_name='typesetting_guide',
        group_name='general',
        values_to_replace=values_to_replace,
        replacement_value=replacement_value,
    )


class Migration(migrations.Migration):

    dependencies = [
        ('utils', '0035_upgrade_1_7_0'),
    ]

    operations = [
        migrations.RunPython(
            update_typesetting_guide,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
