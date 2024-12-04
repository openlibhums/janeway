from django.conf import settings
from django.core.management.base import BaseCommand

from utils.models import RORImport
from core.models import Organization
from utils.logger import get_logger


logger = get_logger(__name__)


class Command(BaseCommand):
    """
    Fetches ROR data and generates Organization records.
    """

    help = "Fetches ROR data and generates Organization records."

    def add_arguments(self, parser):
        parser.add_argument(
            '--test_full_import',
            help='By default, the command only runs 100 records when DEBUG=True.'
                 'Pass --test_full_import to import the entire dump in development.',
            action='store_true',
        )
        return super().add_arguments(parser)

    def handle(self, *args, **options):
        ror_import = RORImport.objects.create()
        ror_import.get_records()

        # The import is necessary.
        # Check we have the right copy of the data dump.
        if ror_import.ongoing or settings.DEBUG:
            if not ror_import.previous_import:
                ror_import.download_data()
            elif ror_import.previous_import.zip_path != ror_import.zip_path:
                ror_import.download_data()

        # The data is all downloaded and ready to import.
        if ror_import.ongoing or settings.DEBUG:
            test_full_import = options.get('test_full_import', False)
            Organization.import_ror_batch(
                ror_import,
                test_full_import=test_full_import,
            )

        # The process did not error out, so it can be considered a success.
        if ror_import.ongoing:
            ror_import.status = ror_import.RORImportStatus.SUCCESSFUL
            ror_import.save()

        logger.info(ror_import.status)
