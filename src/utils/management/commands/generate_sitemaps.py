from django.core.management.base import BaseCommand

from utils import logic


class Command(BaseCommand):
    """CLI interface for generating sitemap files."""

    help = "CLI interface for generating sitemap files."

    def handle(self, *args, **options):
        logic.write_all_sitemaps(cli=True)
