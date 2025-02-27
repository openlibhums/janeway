import os

from django.core.management.base import BaseCommand

from core import plugin_loader
from utils.logger import get_logger

from importlib import import_module

logger = get_logger(__name__)


class Command(BaseCommand):
    """A management command to check for and install new plugins."""

    help = "Checks for new plugins and installs them."

    def add_arguments(self, parser):
        """ Adds arguments to Django's management command-line parser.

        :param parser: the parser to which the required arguments will be added
        :return: None
        """
        parser.add_argument('plugin_name', nargs='?', default=None)

    def handle(self, *args, **options):
        """ Checks for new plugins and installs them.

        :param args: None
        :param options: None
        :return: None
        """

        plugin_name = options.get('plugin_name', None)

        if plugin_name:
            plugin_dirs = [plugin_name]
            homepage_dirs = []
        else:
            plugin_dirs = plugin_loader.get_dirs('plugins')
            homepage_dirs = plugin_loader.get_dirs(
                os.path.join('core', 'homepage_elements'),
            )

        for plugin in plugin_dirs:
            logger.debug('Checking plugin {0}'.format(plugin))
            plugin_module_name = "plugins.{0}.plugin_settings".format(plugin)
            plugin_settings = import_module(plugin_module_name)
            plugin_settings.install()

        for plugin in homepage_dirs:
            logger.debug('Checking plugin {0}'.format(plugin))
            plugin_module_name = "core.homepage_elements.{0}.plugin_settings".format(plugin)
            plugin_settings = import_module(plugin_module_name)
            plugin_settings.install()
