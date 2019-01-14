from __future__ import unicode_literals

from django.db import migrations, connection


def set_default_news_items(apps, schema_editor):
    Plugin = apps.get_model("utils", "Plugin")
    Journal = apps.get_model("journal", "Journal")
    PluginSetting = apps.get_model("utils", "PluginSetting")
    PluginSettingValue = apps.get_model("utils", "PluginSettingValue")

    try:
        plugin = Plugin.objects.get(name="News")
    except Plugin.DoesNotExist:
        pass
    else:
        journals = Journal.objects.all()
        for journal in journals:

            plugin_setting, c = PluginSetting.objects.get_or_create(
                plugin=plugin,
                name="number_of_articles"
            )

            plugin_setting_value, c = PluginSettingValue.objects.get_or_create(
                setting=plugin_setting,
                journal=journal
            )

            SQL = """
            UPDATE utils_pluginsettingvalue_translation SET
            value = 5 WHERE master_id = {master_id} AND value IS NULL;
            """.format(master_id=plugin_setting_value.pk)

            with connection.cursor() as cursor:
                cursor.execute(SQL)






class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_auto_20181116_1123'),
        ('utils', '0009_auto_20180808_1514'),
    ]

    operations = [
        migrations.RunPython(
            set_default_news_items,
            reverse_code=migrations.RunPython.noop
        ),
    ]
