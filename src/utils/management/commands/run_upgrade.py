from importlib import import_module

from django.core.management.base import BaseCommand
from django.utils import translation


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
        parser.add_argument('upgrade_module')

    def handle(self, *args, **options):
        translation.activate('en')
        upgrade_module_name = options.get('upgrade_module')
        upgrade_module_path = 'utils.upgrade.{module_name}'.format(module_name=upgrade_module_name)

        upgrade_module = import_module(upgrade_module_path)
        upgrade_module.execute()

