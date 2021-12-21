from django.core.management.base import BaseCommand
from django.utils import translation

from utils import install


class Command(BaseCommand):
    """ Loads the default values for Janeway settings """

    help = ("Loads the default values for Janeway settings. "
        "If ran multiple times, it will only load missing entries")

    def add_arguments(self, parser):
        parser.add_argument('--force_update',
                            action='store_true',
                            dest='force_update',
                            default=False,
                            help='Resets all of the default settings from the value in JSON.')

    def handle(self, *args, **options):

        translation.activate('en')
        install.update_settings(
            management_command=True,
            overwrite_with_defaults=options.get('force_update', False),
        )
