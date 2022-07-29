import os

from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.shortcuts import reverse
from django.conf import settings

from journal import models as journal_models
from press import models as press_models
from repository import models as repo_models


class Command(BaseCommand):
    """Generates robots.txt files."""

    help = "Generates robots.txt files."

    def handle(self, *args, **options):

        site_map_path = reverse(
            'website_sitemap',
        )
        storage_path = os.path.join(
            settings.BASE_DIR,
            'files',
            'robots',
        )
        if not os.path.exists(storage_path):
            os.makedirs(storage_path)

        press = press_models.Press.objects.all().first()
        press_url = press.site_url(
            path=site_map_path,
        )
        press_robots_txt = render_to_string(
            'common/robots.txt',
            {'url': press_url},
        )

        file_path = os.path.join(
            storage_path,
            'robots.txt'
        )
        with open(file_path, 'w+') as file:
            file.write(press_robots_txt)
            file.close()

        if settings.URL_CONFIG == 'domain':
            domain_mode_journals = journal_models.Journal.objects.filter(
                domain__isnull=False,
            )
            for journal in domain_mode_journals:
                journal_url = journal.site_url(
                    path=site_map_path,
                )
                journal_robots_txt = render_to_string(
                    'common/robots.txt',
                    {'url': journal_url}
                )
                file_path = os.path.join(
                    storage_path,
                    'journal_{}_robots.txt'.format(journal.code)
                )
                with open(file_path, 'w') as file:
                    file.write(journal_robots_txt)
                    file.close()

            domain_mode_repos = repo_models.Repository.objects.filter(
                domain__isnull=False,
            )
            for repo in domain_mode_repos:
                repo_url = repo.site_url(
                    path=site_map_path,
                )
                repo_robots_txt = render_to_string(
                    'common/robots.txt',
                    {'url': repo_url}
                )
                file_path = os.path.join(
                    storage_path,
                    'repo_{}_robots.txt'.format(repo.code)
                )
                with open(file_path, 'w') as file:
                    file.write(repo_robots_txt)
                    file.close()