from django.core.management.base import BaseCommand

from cms import logic as cms_logic
from utils.logger import get_logger

logger = get_logger(__name__)


class Command(BaseCommand):
    help = 'Deletes documents and index files for lunr site search'

    def add_arguments(self, parser):
        parser.add_argument('press_id', type=int)

    def handle(self, *args, **options):
        files_deleted = cms_logic.delete_index(press_id=options['press_id'])
        if files_deleted:
            logger.info(
                self.style.SUCCESS(
                    'Deleted files: ' + ', '.join(files_deleted)
                )
            )
        else:
            logger.info(
                self.style.WARNING(
                    'No index files found'
                )
            )
