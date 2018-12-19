from __future__ import unicode_literals

from django.db import migrations
from utils import setting_handler


def set_default_news_items(apps, schema_editor):
    Plugin = apps.get_model("utils", "Plugin")
    Journal = apps.get_model("journal", "Journal")
    try:
        news_plugin = Plugin.objects.get(name="News")
    except Plugin.DoesNotExist:
        pass
    else:
        journals = Journal.objects.all()
        for journal in journals:
            number_of_articles = setting_handler.get_plugin_setting(
                    plugin=news_plugin.pk,
                    setting_name='number_of_articles',
                    journal=journal.pk,
                    create=True,
                    pretty='Number of Articles',
            ).value
            if number_of_articles in {None, "", " "}:

                setting_handler.save_plugin_setting(
                        plugin=news_plugin,
                        setting_name='number_of_articles',
                        value=5,
                        journal=journal,
                )


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_auto_20181116_1123'),
    ]

    operations = [
        migrations.RunPython(
            set_default_news_items,
            reverse_code=migrations.RunPython.noop
        ),
    ]
