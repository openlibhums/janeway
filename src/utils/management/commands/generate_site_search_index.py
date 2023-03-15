from django.core.management.base import BaseCommand

from cms import logic as cms_logic
from utils.logger import get_logger

logger = get_logger(__name__)


class Command(BaseCommand):
    help = 'Generates a new site search index and saves it as a MediaFile'

    def handle(self, *args, **options):
        documents, index_file = cms_logic.update_index()
        logger.info(
            self.style.SUCCESS(
                f'Successfully updated {documents} and {index_file}'
            )
        )
