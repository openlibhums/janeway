from django.core.management.base import BaseCommand

from cms import logic as cms_logic
from utils.logger import get_logger
from press import models as press_models

logger = get_logger(__name__)


class Command(BaseCommand):
    help = 'Deletes files used by MiniSearch site search'

    def add_arguments(self, parser):
        parser.add_argument('--press_id', type=int)

    def handle(self, *args, **options):
        if options['press_id']:
            press = press_models.Press.objects.get(pk=options['press_id'])
        else:
            press = press_models.Press.objects.first()
        files_deleted = cms_logic.delete_search_data(press)

        if files_deleted:
            logger.debug(
                self.style.SUCCESS(
                    'Deleted files: ' + ', '.join(files_deleted)
                )
            )
        else:
            logger.warning(
                self.style.WARNING(
                    'No search data files found'
                )
            )
