from django.core.management.base import BaseCommand
from django.utils import translation

from utils.importers.up import (
    scrape_editorial_team,
    scrape_policies_page,
    scrape_submissions_page,
    scrape_about_page,
    scrape_research_integrity_page,
)
from journal import models


class Command(BaseCommand):
    """
    Fetches a backend article from a UP journal
    """

    help = "Fetches front end minutia from a UP site."

    def add_arguments(self, parser):
        """Adds arguments to Django's management command-line parser.

        :param parser: the parser to which the required arguments will be added
        :return: None
        """
        parser.add_argument("base_url", default=None)
        parser.add_argument("journal_code", default=None)

    def handle(self, *args, **options):
        translation.activate("en")
        try:
            journal = models.Journal.objects.get(code=options.get("journal_code"))
            print("Scraping into {}".format(journal.name))
            scrape_editorial_team(journal, options.get("base_url"))
            scrape_policies_page(
                journal,
                options.get("base_url"),
            )
            scrape_submissions_page(journal, options.get("base_url"))
            scrape_research_integrity_page(
                journal,
                options.get("base_url"),
            )
            scrape_about_page(
                journal,
                options.get("base_url"),
            )

        except models.Journal.DoesNotExist:
            exit("[Error] No journal found with that code.")
