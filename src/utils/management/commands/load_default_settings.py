from django.core.management.base import BaseCommand
from django.utils import translation

from utils import install


class Command(BaseCommand):
    """ Loads the default values for Janeway settings """

    help = ("Loads the default values for Janeway settings. "
        "If ran multiple times, it will only load missing entries")

    def handle(self, *args, **options):

        translation.activate('en')
        install.update_settings(management_command=True)
