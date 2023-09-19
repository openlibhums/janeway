from django.core.management.base import BaseCommand

from cms import logic as cms_logic
from utils.logger import get_logger

logger = get_logger(__name__)


class Command(BaseCommand):
    help = 'Deletes files used by MiniSearch site search'

    def add_arguments(self, parser):
        parser.add_argument('--press_id', type=int)

    def handle(self, *args, **options):
        if options['press_id']:
            files_deleted = cms_logic.delete_search_data(press_id=options['press_id'])
        else:
            files_deleted = cms_logic.delete_search_data()

        if files_deleted:
            logger.info(
                self.style.SUCCESS(
                    'Deleted files: ' + ', '.join(files_deleted)
                )
            )
        else:
            logger.info(
                self.style.WARNING(
                    'No search data files found'
                )
            )
