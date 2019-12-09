from django.core.management.base import BaseCommand

from journal.logic import merge_sections
from submission import models as submission_models


class Command(BaseCommand):
    """ Merges the articles from a list of issues into the destination"""

    help = "Merges issues by moving the content from the issues to the "
    "destination issue and deletes the merged issues"

    def add_arguments(self, parser):
        parser.add_argument('destination_id')
        parser.add_argument('-s', '--section-ids',
                            nargs='+',
                            )

    def handle(self, *args, **options):
        section_ids = options["section_ids"]
        if section_ids:
            destination_id = options["destination_id"]
            if destination_id in section_ids:
                raise RuntimeError("Can't merge a section with itself")
            sections = submission_models.Section.objects.filter(
                pk__in=section_ids)
            destination = submission_models.Section.objects.get(
                pk=destination_id)
            merge_sections(destination, sections)
