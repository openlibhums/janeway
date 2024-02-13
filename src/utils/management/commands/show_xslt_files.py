from django.core.management.base import BaseCommand

from journal import models
from core import models as core_models


class Command(BaseCommand):
    """Lists XSL Files"""

    help = "Lists XSL Files"

    def handle(self, *args, **options):
        """
        Lists XSL Files
        """
        xsl_files = core_models.XSLFile.objects.all().order_by(
            '-pk'
        )

        for file in xsl_files:
            print(
                f"{file.pk} - {file.label} [{file.date_uploaded}] linked to {file.journal.name if file.journal else 'No Journal'}"
            )


