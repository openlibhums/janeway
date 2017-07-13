from importlib import import_module

from django.core.management.base import BaseCommand

from core import logic


class Command(BaseCommand):
    """A management command to build all assets across the platform's themes.."""

    help = "Synchronizes unspecified default settings to all journals."

    def handle(self, *args, **options):
        themes = logic.get_theme_list()

        for theme in themes:
            module_name = "themes.{0}.build_assets".format(theme[0])
            builder = import_module(module_name)
            builder.build()
