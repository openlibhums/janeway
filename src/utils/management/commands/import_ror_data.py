from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

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
            "--limit",
            help="The cap on the number of ROR records to process.",
            default=0,
            type=int,
        )
        return super().add_arguments(parser)

    def handle(self, *args, **options):
        limit = options.get("limit", 0)
        if not limit and settings.DEBUG:
            limit = 100
            logger.info(
                f"Setting ROR import limit to {limit} while settings.DEBUG. "
                "Override by passing --limit to import_ror_data."
            )

        ror_import = RORImport.objects.create()
        ror_import.get_records()

        # The import is necessary.
        # Check we have the right copy of the data dump.
        if ror_import.is_ongoing:
            if not ror_import.previous_import:
                ror_import.download_data()
            elif ror_import.previous_import.zip_path != ror_import.zip_path:
                ror_import.download_data()
            else:
                logger.debug("The latest ROR data has already been downloaded")

        # The data is all downloaded and ready to import.
        if ror_import.is_ongoing:
            Organization.objects.manage_ror_import(
                ror_import,
                limit=limit,
            )
        logger.debug(
            f'ROR import exited with status: '
            f'{ ror_import.get_status_display() }'
        )
