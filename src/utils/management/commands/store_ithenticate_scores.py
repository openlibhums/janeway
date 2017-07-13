from django.core.management.base import BaseCommand

from submission import models
from journal import models as journal_models
from utils import ithenticate


class Command(BaseCommand):
    """Fetches ithenticate scores for articles."""

    help = "Fetches ithenticate scores for articles."

    def handle(self, *args, **options):
        """Fetches and saves ithenticate scores for articles

        :param args: None
        :param options: Dictionary containing 'doi_suffix'
        :return: None
        """
        for journal in journal_models.Journal.objects.all():

            print("Processing journal {0}...".format(journal.name))
            articles = models.Article.objects.filter(journal=journal, ithenticate_id__isnull=False)
            ithenticate.fetch_percentage(journal, articles)
