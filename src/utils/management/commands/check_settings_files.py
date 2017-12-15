import codecs
import os
import json

from django.core.management.base import BaseCommand
from django.utils import translation
from django.conf import settings


def update_default_setting(default_data, db_setting):
    for default_setting in default_data:
        if default_setting['setting'].get('name') == db_setting.setting.name and default_setting['group'].get('name') == db_setting.setting.group.name:
            print('Updating {0}'.format(db_setting.setting.name))
            default_setting['setting']['value'] = db_setting.value


class Command(BaseCommand):
    """A management command to synchronize all default settings to all journals."""

    help = "Synchronizes unspecified default settings to all journals."

    def handle(self, *args, **options):
        translation.activate('en')

        with codecs.open(os.path.join(settings.BASE_DIR, 'utils/install/journal_defaults.json'), 'r+', encoding='utf-8') as json_data:
            default_data = json.load(json_data)

        with codecs.open(os.path.join(settings.BASE_DIR, 'utils/install/test.json'), 'r+', encoding='utf-8') as test_json_data:
            test_data = json.load(test_json_data)

        print(len(default_data))
        print(len(test_data))

        for setting in default_data:
            setting_name = setting['setting']['name']
            found = False

            for test_setting in test_data:
                test_setting_name = setting['setting']['name']
                if test_setting_name == setting_name:
                    found = True

            if found:
                print('{0} found'.format(setting_name))
            else:
                print('{0} not found'.format(setting_name))
