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
            '--codes',
            nargs='+',
            help='The codes of the sites (empty for all sites)',
        )

    def handle(self, *args, **options):
        site_type = options.get('site_type')
        codes = options.get('codes')

        journals = journal_models.Journal.objects.none()
        repositories = repository_models.Repository.objects.none()

        if site_type == 'journals' or not site_type:
            journals = journal_models.Journal.objects.all()
        if site_type == 'repositories' or not site_type:
            repositories = repository_models.Repository.objects.all()

        if codes:
            repositories = repositories.filter(short_name__in=codes)
            journals = journals.filter(code__in=codes)

        # Generate the press level sitemap
        print("Generating sitemap for press")
        logic.write_press_sitemap()

        # Generate Journal Sitemaps
        if journals:
            print("Generating sitemaps for journals")
            for journal in journals:
                if journal.published_issues:
                    print(f"Generating sitemaps for {journal.name}'s issues:")
                    logic.write_journal_sitemap(journal)

                    # Generate Issue Sitemap
                    for issue in tqdm(journal.published_issues):
                        logic.write_issue_sitemap(issue)

        # Generate Repo Sitemap
        if repositories:
            print("Generating sitemaps for repositories")
            for repo in repositories:
                if repo.subject_set.all():
                    print(f"Generating sitemaps for {repo.name}'s subjects:")
                    logic.write_repository_sitemap(repo)

                    for subject in tqdm(repo.subject_set.all()):
                        logic.write_subject_sitemap(subject)

