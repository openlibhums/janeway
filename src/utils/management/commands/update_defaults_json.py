import codecs
import json
import os

from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    """
    A reusable command for editing defaults.json
    """

    help = "Deletes duplicate settings."

    def handle(self, *args, **options):
        """A reusable command for editing defaults.json

        :param args: None
        :param options: None
        :return: None
        """
        with codecs.open(os.path.join(settings.BASE_DIR, 'utils/install/journal_defaults.json'),
                         encoding='utf-8') as json_data:
            default_data = json.load(json_data)

            for item in default_data:

                if item['group'].get('name') == 'email':
                    item['setting']['is_translatable'] = True
                elif item['setting'].get('type') == 'rich-text' or item['setting'].get('type') == 'char' or item['setting'].get('type') == 'text'or item['setting'].get('type') == 'json':
                    item['setting']['is_translatable'] = True
                else:
                    item['setting']['is_translatable'] = False

            write_path = os.path.join(settings.BASE_DIR, 'utils/install/journal_defaults.json')
            with open(write_path, 'w+', encoding="utf-8") as f:
                f.write(json.dumps(default_data, indent=4, sort_keys=True))
