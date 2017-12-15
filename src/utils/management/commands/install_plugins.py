import os

from django.core.management.base import BaseCommand

from core import plugin_loader

from importlib import import_module


class Command(BaseCommand):
    """A management command to check for and install new plugins."""

    help = "Checks for new plugins and installs them."

    def handle(self, *args, **options):
        """ Checks for new plugins and installs them.

        :param args: None
        :param options: None
        :return: None
        """
        plugin_dirs = plugin_loader.get_dirs('plugins')
        homepage_dirs = plugin_loader.get_dirs(os.path.join('core', 'homepage_elements'))

        for plugin in plugin_dirs:
            print('Checking plugin {0}'.format(plugin))
            plugin_module_name = "plugins.{0}.plugin_settings".format(plugin)
            plugin_settings = import_module(plugin_module_name)
            plugin_settings.install()

        for plugin in homepage_dirs:
            print('Checking plugin {0}'.format(plugin))
            plugin_module_name = "core.homepage_elements.{0}.plugin_settings".format(plugin)
            plugin_settings = import_module(plugin_module_name)
            plugin_settings.install()
