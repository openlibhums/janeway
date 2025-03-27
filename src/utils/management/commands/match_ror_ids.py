from django.conf import settings
from django.core.management.base import BaseCommand

from datetime import timedelta

from utils.models import RORImport
from core.models import Organization
from utils.logger import get_logger
from django.utils import timezone


logger = get_logger(__name__)


class Command(BaseCommand):
    """
    Matches organization names and countries with ROR data.
    """

    help = "Matches organization records with ROR data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            help="The cap on the number of organizations to deduplicate.",
            default=0,
            type=int,
        )
        parser.add_argument(
            '--ignore_missing_import',
            help='Run the match even if no ROR import is found',
            action='store_true',
        )
        return super().add_arguments(parser)

    def handle(self, *args, **options):
        limit = options.get("limit", 0)
        ror_import = RORImport.objects.filter(
            started__gte=timezone.now() - timedelta(days=90)
        ).exists()
        ignore_missing_import = options.get("ignore_missing_import")
        if not ror_import and not ignore_missing_import:
            logger.warning(
                "There was no ROR import in the last 90 days."
                "Run import_ror_data before continuing,"
                "or pass --ignore_missing_import."
            )
            return
        Organization.objects.all().deduplicate_to_ror(limit=limit)
