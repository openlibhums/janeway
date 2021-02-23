import codecs
import os
import json
from collections import OrderedDict

from django.core.management.base import BaseCommand
from django.utils import translation
from django.conf import settings

from journal import models as journal_models
from core import models as core_models


def update_default_setting(default_data, db_setting):
    for default_setting in default_data:
        if default_setting['setting'].get('name') == db_setting.setting.name and \
                default_setting['group'].get('name') == db_setting.setting.group.name:
            print('Updating {0}'.format(db_setting.setting.name))
            default_setting['value']['default'] = db_setting.value


class Command(BaseCommand):
    """A management command to synchronize all default settings to all journals."""

    help = "Synchronizes unspecified default settings to all journals."

    def add_arguments(self, parser):
        """ Adds arguments to Django's management command-line parser.

        :param parser: the parser to which the required arguments will be added
        :return: None
        """
        parser.add_argument('--journal_code', default=None)
        parser.add_argument('--group_name', nargs='?', default=None)
        parser.add_argument('--setting_name', nargs='?', default=None)

    def handle(self, *args, **options):
        """Synchronizes settings to journals.

        :param args: None
        :param options: None
        :return: None
        """
        translation.activate('en')
        journal_code = options.get('journal_code', None)
        group_name = options.get('group_name', None)
        setting_name = options.get('setting_name', None)

        if journal_code:
            journal = journal_models.Journal.objects.get_or(code=journal_code)
        else:
            journal = None

        if not group_name and not setting_name:
            setting_list = core_models.SettingValue.objects.filter(
                journal=journal
            )

        if group_name:
            setting_list = core_models.SettingValue.objects.filter(
                setting__group__name=group_name,
                journal=journal
            )

        if setting_name:
            setting_list = core_models.SettingValue.objects.filter(
                setting__group__name=group_name,
                setting__name=setting_name,
                journal=journal
            )

        with codecs.open(os.path.join(settings.BASE_DIR, 'utils/install/journal_defaults.json'), 'r+', encoding='utf-8') as json_data:
            default_data = json.load(json_data, object_pairs_hook=OrderedDict)

            for setting in setting_list:
                update_default_setting(default_data, setting)

            json_data.seek(0)
            json_data.write(json.dumps(default_data, indent=4))
