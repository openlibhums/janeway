from django.core.management.base import BaseCommand

from journal import models as journal_models


class Command(BaseCommand):
    """Turns off Subtitle field for all journals."""

    help = "Turns off the Subtitle field for all journals."

    def handle(self, *args, **options):
        for journal in journal_models.Journal.objects.all():
            if hasattr(journal, 'submissionconfiguration'):
                journal.submissionconfiguration.subtitle = False
                journal.submissionconfiguration.save()
