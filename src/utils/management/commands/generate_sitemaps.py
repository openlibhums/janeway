import os

from django.core.management.base import BaseCommand
from django.conf import settings
from django.template.loader import render_to_string

from journal import models as journal_models
from repository import models as repo_models


class Command(BaseCommand):
    """Turns off Subtitle field for all journals."""

    help = "Turns off the Subtitle field for all journals."

    def handle(self, *args, **options):

        storage_path = os.path.join(
            settings.BASE_DIR,
            'files',
            'sitemaps',
        )
        if not os.path.exists(storage_path):
            os.makedirs(storage_path)

        # Generate the press level sitemap
        journals = journal_models.Journal.objects.all()
        repos = repo_models.Repository.objects.all()
        site_map_index = render_to_string(
            'common/site_map_index.xml',
            {
                'journals': journals,
                'repos': repos,
            }
        )
        file_path = os.path.join(
            storage_path,
            'sitemap.xml'
        )
        with open(file_path, 'w+') as file:
            file.write(site_map_index)
            file.close()

        # Generate Journal Sitemaps
        for journal in journals:
            print("Generating sitemaps for {}".format(journal.name))
            journal_site_map = render_to_string(
                'common/journal_sitemap.xml',
                {
                    'journal': journal,
                }
            )
            journal_storage_path = os.path.join(
                storage_path,
                journal.code,
            )
            if not os.path.exists(journal_storage_path):
                os.makedirs(journal_storage_path)

            journal_file_path = os.path.join(
                journal_storage_path,
                'sitemap.xml'
            )
            with open(journal_file_path, 'w') as file:
                file.write(journal_site_map)
                file.close()

            # Generate Issue Sitemap
            for issue in journal.published_issues:
                issue_sitemap = render_to_string(
                    'common/issue_sitemap.xml',
                    {'issue': issue},
                )
                issue_file_path = os.path.join(
                    journal_storage_path,
                    '{}_sitemap.xml'.format(issue.pk)
                )
                with open(issue_file_path, 'w') as file:
                    file.write(issue_sitemap)
                    file.close()

        # Generate Repo Sitemap
        for repo in repos:
            print("Generating sitemaps for {}".format(repo.name))
            repo_site_map = render_to_string(
                'common/repo_sitemap.xml',
                {
                    'repo': repo,
                }
            )
            repo_storage_path = os.path.join(
                storage_path,
                repo.code,
            )
            if not os.path.exists(repo_storage_path):
                os.makedirs(repo_storage_path)

            repo_file_path = os.path.join(
                repo_storage_path,
                'sitemap.xml'
            )
            with open(repo_file_path, 'w') as file:
                file.write(repo_site_map)
                file.close()

            for subject in repo.subject_set.all():
                subject_sitemap = render_to_string(
                    'common/subject_sitemap.xml',
                    {'subject': subject},
                )
                subject_file_path = os.path.join(
                    repo_storage_path,
                    '{}_sitemap.xml'.format(subject.pk)
                )
                with open(subject_file_path, 'w') as file:
                    file.write(subject_sitemap)
                    file.close()
