
from django.core.management.base import BaseCommand
from django.utils import translation

from utils.importers.up import scrape_cms_page
from journal import models


class Command(BaseCommand):
    """
    Scrapes a given CMS page from an UP journal
    """
    help = "Scrapes a given CMS page from an UP journal"

    def add_arguments(self, parser):
        """Adds arguments to Django's management command-line parser.

        :param parser: the parser to which the required arguments will be added
        :return: None
        """
        parser.add_argument('page_url', default=None)
        parser.add_argument(
            'page_name',
            help="The display name for the page in Janeway",
        )
        parser.add_argument('journal_code', default=None)

    def handle(self, *args, **options):
        translation.activate('en')
        try:
            journal = models.Journal.objects.get(
                code=options.get('journal_code')
            )
        except models.Journal.DoesNotExist:
            exit('[Error] No journal found with that code.')
        else:
            print('Scraping into {}'.format(journal.name))
            scrape_cms_page(journal, options["page_url"], options["page_name"])

