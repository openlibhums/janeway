from django.core.management.base import BaseCommand

from journal import models
from journal.logic import merge_issues


class Command(BaseCommand):
    """ Merges the articles from a list of issues into the destination"""

    help = "Merges issues by moving the content from the issues to the "
    "destination issue and deletes the merged issues"

    def add_arguments(self, parser):
        parser.add_argument('destination_id')
        parser.add_argument('-i', '--issue-ids',
                            nargs='+',
                            )

    def handle(self, *args, **options):
        issue_ids = options["issue_ids"]
        if issue_ids:
            destination_id = options["destination_id"]
            if destination_id in issue_ids:
                raise RuntimeError("Can't merge an issue with itself")
            issues = models.Issue.objects.filter(pk__in=issue_ids)
            destination = models.Issue.objects.get(pk=destination_id)
            merge_issues(destination, issues)


