from django.core.management.base import BaseCommand

from submission import models
from journal import models as journal_models
from utils import ithenticate


class Command(BaseCommand):
    """Fetches ithenticate scores for articles."""

    help = "Fetches ithenticate scores for articles."

    def handle(self, *args, **options):
        for journal in journal_models.Journal.objects.filter(is_remote=False):

            if ithenticate.ithenticate_is_enabled(journal):
                print("Processing journal {0}...".format(journal.name))
                articles = models.Article.objects.filter(
                    journal=journal,
                    ithenticate_id__isnull=False,
                    ithenticate_score__isnull=True,
                )
                ithenticate.fetch_percentage(journal, articles)
            else:
                print('Ithenticate is not enabled for {journal}. Skipping.'.format(journal=journal.name))
