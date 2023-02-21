from django.core.management.base import BaseCommand

from utils import shared


class Command(BaseCommand):
    """Clears the Django cache."""

    help = "Clears the Django cache.."

    def handle(self, *args, **options):
        shared.clear_cache()