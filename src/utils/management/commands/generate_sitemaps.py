from django.core.management.base import BaseCommand

from utils import logic

def str2bool(s):
    lower = s.lower()
    assert(lower == 'true' or lower == 'false')
    return lower == 'true'

class Command(BaseCommand):
    """CLI interface for generating sitemap files."""

    help = "CLI interface for generating sitemap files."

    def add_arguments(self, parser):
        """Adds arguments to Django's management command-line parser.

        :param parser: the parser to which the required arguments will be added
        :return: None
        """
        parser.add_argument('-p', '--press', default=True, type=str2bool)
        parser.add_argument('-j', '--journal', default=True, type=str2bool)
        parser.add_argument('-r', '--repository', default=True, type=str2bool)

    def handle(self, *args, **options):
        logic.write_all_sitemaps(cli=True, press_sitemap=options['press'], journal_sitemap=options['journal'], repository_sitemap=options['repository'])
