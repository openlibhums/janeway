from django.core.management.base import BaseCommand

from cms import logic as cms_logic
from utils.logger import get_logger

logger = get_logger(__name__)


class Command(BaseCommand):
    help = 'Generates new site search data and saves it as a MediaFile'

    def add_arguments(self, parser):
        parser.add_argument('--press_id', type=int)

    def handle(self, *args, **options):
        if options['press_id']:
            documents = cms_logic.update_search_data(press_id=options['press_id'])
        else:
            documents = cms_logic.update_search_data()
        logger.info(
            self.style.SUCCESS(
                f'Successfully updated {documents}'
            )
        )
