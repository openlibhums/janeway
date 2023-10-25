import os
from importlib import import_module

from django.core.management.base import BaseCommand
from django.utils import translation
from django.conf import settings


def get_modules():
    path = os.path.join(settings.BASE_DIR, 'utils', 'upgrade')
    root, dirs, files = next(os.walk(path))
    return files


class Command(BaseCommand):
    """
    Upgrades Janeway
    """

    help = "Upgrades an install from one version to another."

    def add_arguments(self, parser):
        """Adds arguments to Django's management command-line parser.

        :param parser: the parser to which the required arguments will be added
        :return: None
        """
        parser.add_argument('--path', required=False)

    def handle(self, *args, **options):

        raise DeprecationWarning('This command is deprecated. Use the update script .update.sh')
        if not options.get('path'):
            print('No upgrade selected. Available upgrade paths: ')
            for file in get_modules():
                module_name = file.split('.')[0]
                print('- {module_name}'.format(module_name=module_name))
                print('To run an upgrade use the following: `python3 manage.py run_upgrade --script 12_13`')
        else:
            translation.activate('en')
            upgrade_module_name = options.get('path')
            upgrade_module_path = 'utils.upgrade.{module_name}'.format(module_name=upgrade_module_name)

            try:
                upgrade_module = import_module(upgrade_module_path)
                upgrade_module.execute()
            except ImportError as e:
                print('There was an error running the requested upgrade: ')
                print(e)
