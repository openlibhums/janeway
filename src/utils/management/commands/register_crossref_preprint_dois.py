from django.core.management.base import BaseCommand

from identifiers import preprints
from repository import models


class Command(BaseCommand):
    """Registers a repository object version with Crossref."""

    help = "Registers a repository object version with Crossref."

    def add_arguments(self, parser):
        """Adds arguments to Django's management command-line parser.

        :param parser: the parser to which the required arguments will be added
        :return: None
        """
        parser.add_argument('version_id')

    def handle(self, *args, **options):
        """Calls the Crossref registration options

        :param args: None
        :param options: Dictionary containing 'article_id'
        :return: None
        """
        version = models.PreprintVersion.objects.get(
            pk=options.get('version_id')
        )
        if version:
            preprints.deposit_doi_for_preprint_version(
                version.preprint.repository,
                [version],
            )
