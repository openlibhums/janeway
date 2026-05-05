from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import Location, Organization
from utils.logger import get_logger
from utils.models import RORImport, RORImportError


logger = get_logger(__name__)


class Command(BaseCommand):
    """
    Deletes ROR-derived Organization, OrganizationName and Location records,
    plus all RORImport history. Intended for use before re-running
    import_ror_data when the previous import was incomplete or corrupt
    (see issue #5248).

    Custom (user-created) organizations and their custom_label OrganizationName
    rows are preserved. ControlledAffiliation rows pointing at deleted
    organizations have their organization FK set to NULL via on_delete=SET_NULL.
    """

    help = (
        "Delete all ROR-imported Organizations, Locations and import history. "
        "Custom organisations and existing affiliations are preserved."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--no-input",
            action="store_true",
            help="Do not prompt for confirmation before deleting.",
        )
        return super().add_arguments(parser)

    def handle(self, *args, **options):
        ror_orgs = Organization.objects.exclude(ror_id="")
        ror_locations = Location.objects.filter(geonames_id__isnull=False)

        org_count = ror_orgs.count()
        location_count = ror_locations.count()
        import_count = RORImport.objects.count()
        error_count = RORImportError.objects.count()

        self.stdout.write(
            f"This will delete:\n"
            f"  {org_count} ROR Organizations (and their cascade-linked names)\n"
            f"  {location_count} ROR Locations\n"
            f"  {import_count} RORImport records\n"
            f"  {error_count} RORImportError records\n"
        )

        if not options["no_input"]:
            confirm = input("Continue? [y/N] ").strip().lower()
            if confirm != "y":
                self.stdout.write("Aborted.")
                return

        with transaction.atomic():
            RORImportError.objects.all().delete()
            RORImport.objects.all().delete()
            ror_orgs.delete()
            ror_locations.delete()

        self.stdout.write(self.style.SUCCESS("ROR data cleared."))
