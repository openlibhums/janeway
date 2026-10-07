from django.db import migrations


def delete_crosscheck_settings(apps, schema_editor):
    """Remove the settings for the old iThenticate integration, which has
    been replaced by the Turnitin Core API plugin."""
    Setting = apps.get_model("core", "Setting")
    SettingGroup = apps.get_model("core", "SettingGroup")
    Setting.objects.filter(group__name="crosscheck").delete()
    SettingGroup.objects.filter(name="crosscheck").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0111_merge_20260603_2206"),
    ]

    operations = [
        migrations.RunPython(
            delete_crosscheck_settings,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
