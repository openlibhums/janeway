import os
from tqdm import tqdm

from django.core.management.base import BaseCommand

from utils import logic
from utils.management.base import ProfiledCommand
from journal import models as journal_models
from repository import models as repository_models
from press import models as press_models


class Command(ProfiledCommand):
    """CLI interface for generating sitemap files."""

    help = "CLI interface for generating sitemap files."

    def add_arguments(self, parser):
        """Adds arguments to Django's management command-line parser.

        :param parser: the parser to which the required arguments will be added
        :return: None
        """
        super().add_arguments(parser)
        parser.add_argument(
            '--site_type',
            choices=['journals', 'repositories'],
            help='The type of site, either journals or repositories',

        )
        parser.add_argument(
            '--ids',
            nargs='+',
            help='The IDs of the sites or "all"',
        )
        parser.add_argument(
            '--codes',
            nargs='+',
            help='The codes of the sites (empty for all sites)',
        )

    def handle(self, *args, **options):
        obj_type = options['site_type']
        obj_ids = options['ids']

        journals, repositories, all_sites = None, None, False

        if obj_ids and obj_ids[0] == 'all':
            all_sites = True

        if obj_type == 'journals':
            journals = journal_models.Journal.objects.all()
            if not all_sites:
                journals = journals.filter(id__in=obj_ids)
        elif obj_type == 'repositories':
            repositories = repository_models.Repository.objects.all()
            if not all_sites:
                repositories = repositories.filter(id__in=obj_ids)
        else:
            # no obj_type assumes that all site types run have been requested.
            repositories = repository_models.Repository.objects.all()
            journals = journal_models.Journal.objects.all()
            if options["codes"]:
                repositories = repositories.filter(short_name__in=options["codes"])
                journals = journals.filter(code__in=options["codes"])

        # Generate the press level sitemap
        print("Generating sitemap for press")
        logic.write_press_sitemap()

        # Generate Journal Sitemaps
        if journals:
            print("Generating sitemaps for journals")
            for journal in tqdm(journals):
                logic.write_journal_sitemap(journal)

                # Generate Issue Sitemap
                for issue in journal.published_issues:
                    logic.write_issue_sitemap(issue)

        # Generate Repo Sitemap
        if repositories:
            print("Generating sitemaps for repositories")
            for repo in tqdm(repositories):
                logic.write_repository_sitemap(repo)

                for subject in repo.subject_set.all():
                    logic.write_subject_sitemap(subject)

