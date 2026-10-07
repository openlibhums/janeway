from django.core.management.base import BaseCommand

from submission import models
from journal import models as journal_models
from utils import ithenticate
from utils.logger import get_logger

logger = get_logger(__name__)


class Command(BaseCommand):
    """Fetches ithenticate scores for articles."""

    help = "Fetches ithenticate scores for articles."

    def handle(self, *args, **options):
        for journal in journal_models.Journal.objects.filter(
            is_remote=False,
        ).exclude(
            status=journal_models.Journal.PublishingStatus.TEST,
        ):
            if ithenticate.ithenticate_is_enabled(journal):
                print("Processing journal {0}...".format(journal.name))
                articles = models.Article.objects.filter(
                    journal=journal,
                    ithenticate_id__isnull=False,
                    ithenticate_score__isnull=True,
                )
                if not articles.exists():
                    continue
                try:
                    ithenticate.fetch_percentage(journal, articles)
                except AssertionError:
                    logger.warning(
                        "Ithenticate login failed for {journal}. Skipping.".format(
                            journal=journal.name,
                        )
                    )
            else:
                print(
                    "Ithenticate is not enabled for {journal}. Skipping.".format(
                        journal=journal.name
                    )
                )
