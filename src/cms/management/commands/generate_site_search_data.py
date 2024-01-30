from django.core.management.base import BaseCommand

from cms import logic as cms_logic
from utils.logger import get_logger
from press import models as press_models

logger = get_logger(__name__)


class Command(BaseCommand):
    help = 'Generates new site search data and saves it as a MediaFile'

    def add_arguments(self, parser):
        parser.add_argument('--press_id', type=int)

    def handle(self, *args, **options):
        if options['press_id']:
            press = press_models.Press.objects.get(pk=options['press_id'])
        else:
            press = press_models.Press.objects.first()
        documents = cms_logic.update_search_data(press)
        logger.debug(
            self.style.SUCCESS(
                f'Successfully updated {documents}'
            )
        )
