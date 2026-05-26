from tqdm import tqdm

from django.conf import settings
from django.utils import translation

from utils import logic
from utils.management.base import ProfiledCommand
from journal import models as journal_models
from repository import models as repository_models
from press import models as press_models


def _filter(qs, site_type, my_site_type, codes, code_field):
    if site_type and site_type != my_site_type:
        return qs.none()
    if codes:
        qs = qs.filter(**{f"{code_field}__in": codes})
    return qs


class Command(ProfiledCommand):
    """CLI interface for generating sitemap files."""

    help = "CLI interface for generating sitemap files."

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "--site_type",
            choices=["journals", "repositories"],
            help="The type of site, either journals or repositories",
        )
        parser.add_argument(
            "--codes",
            nargs="+",
            help="The codes of the sites (empty for all sites)",
        )

    def handle(self, *args, **options):
        with translation.override(settings.LANGUAGE_CODE):
            site_type = options.get("site_type")
            codes = options.get("codes")

            journals = _filter(
                journal_models.Journal.objects.all(),
                site_type,
                "journals",
                codes,
                "code",
            )
            repositories = _filter(
                repository_models.Repository.objects.all(),
                site_type,
                "repositories",
                codes,
                "short_name",
            )
            press = press_models.Press.objects.first()

            # Press level
            if press:
                print("Generating press sitemap")
                logic.write_press_sitemap()
                logic.write_pages_sitemap(press)
                if press.active_news_items.exists():
                    logic.write_news_sitemap(press)

            # Journal level
            for journal in journals:
                print(f"Generating sitemap for {journal.name}")
                regular_issues = logic._journal_regular_issues(journal)
                has_issues_with_articles = any(
                    i.get_sorted_articles().exists() for i in regular_issues
                )
                has_orphans = logic._articles_not_in_any_regular_issue(journal).exists()
                has_news = journal.active_news_items.exists()
                # Canonical pages always include Home and Accessibility
                has_pages = True

                if has_pages or has_issues_with_articles or has_orphans or has_news:
                    logic.write_journal_sitemap(journal)
                    logic.write_pages_sitemap(journal)
                    if has_news:
                        logic.write_news_sitemap(journal)
                    for issue in tqdm(list(regular_issues)):
                        if issue.get_sorted_articles().exists():
                            logic.write_issue_sitemap(issue)
                    if has_orphans:
                        logic.write_not_in_any_issue_sitemap(journal)

            # Repository level
            for repo in repositories:
                print(f"Generating sitemap for {repo.name}")
                subjects = repo.subject_set.all()
                has_subjects_with_preprints = any(
                    s.published_preprints().exists() for s in subjects
                )
                has_orphans = logic._preprints_without_subject(repo).exists()

                if has_subjects_with_preprints or has_orphans:
                    logic.write_repository_sitemap(repo)
                    logic.write_pages_sitemap(repo)
                    for subject in tqdm(list(subjects)):
                        if subject.published_preprints().exists():
                            logic.write_subject_sitemap(subject)
                    if has_orphans:
                        logic.write_not_in_any_subject_sitemap(repo)
