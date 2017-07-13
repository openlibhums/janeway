import os

from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command

from core import plugin_loader


class Command(BaseCommand):
    """A management command to check for and migrate plugins."""

    help = "Migrates plugins"

    def add_arguments(self, parser):
        """ Adds arguments to Django's management command-line parser.

        :param parser: the parser to which the required arguments will be added
        :return: None
        """
        parser.add_argument('--make', action='store_true', default=False)
        parser.add_argument('--migrate', action='store_true', default=False)
        parser.add_argument('--app_name', default=False)

    def handle(self, *args, **options):
        """ A management command to check for and migrate plugins.

        :param args: None
        :param options: None
        :return: None
        """
        all_plugins_to_handle = None

        if not options.get('app_name'):
            plugin_dirs = plugin_loader.get_dirs('plugins')
            homepage_dirs = plugin_loader.get_dirs(os.path.join("core", "homepage_elements"))
            all_plugins_to_handle = plugin_dirs + homepage_dirs

        elif options.get('app_name'):
            all_plugins_to_handle = [options.get('app_name')]

        if all_plugins_to_handle:

            for plugin in all_plugins_to_handle:

                if options.get('make'):
                    call_command('makemigrations', plugin)
                elif options.get('migrate'):
                    try:
                        call_command('migrate', plugin)
                    except CommandError:
                        print('Plugin {0} has no migrations.'.format(plugin))

        else:
            print('Result: Either there are no plugins installed or the app_name you passed doesn\'t exist')
