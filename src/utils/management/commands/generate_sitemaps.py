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


# Fixed-width trailing fields keep every bar the same length: the count and
# rate columns no longer change width line-to-line, so tqdm expands the bar to
# fill the gap and the figures right-align to the line. The leading space on
# the unit (below) puts a gap between the rate number and "sitemap/s".
_BAR_FORMAT = (
    "{desc}: {percentage:3.0f}%|{bar}| "
    "{n_fmt:>4}/{total_fmt:<4} "
    "[{elapsed} < {remaining}, {rate_fmt:>16}]"
)


def _log(message):
    """Console progress line, silenced under the test runner so the suite
    output stays clean."""
    if not settings.IN_TEST_RUNNER:
        print(message)


def _run(children):
    """Write each sub-sitemap of a siteindex, showing progress.

    ``children`` is the list of zero-argument writers for the sub-sitemaps
    referenced by one siteindex. The progress bar counts those sub-sitemaps,
    so every site reports a meaningful, non-zero total (pages is always
    present) rather than tqdm's bare ``0it`` placeholder. The bar is disabled
    under the test runner so it does not spam the test output.
    """
    for write in tqdm(
        children,
        desc="  sub-sitemaps",
        unit=" sitemap",
        bar_format=_BAR_FORMAT,
        disable=settings.IN_TEST_RUNNER,
    ):
        write()


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

            # Remote journals are not hosted in Janeway, so they have no local
            # pages to write a sitemap for. Hidden journals (hide_from_press)
            # are still generated: they have a live site, just no link from the
            # press index (their siteindex has no higher level — see
            # build_journal_index_context).
            journals = _filter(
                journal_models.Journal.objects.filter(is_remote=False),
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
                _log("Generating press sitemap")
                # Sub-sitemaps written into the press siteindex. Journals and
                # repositories are also referenced by the index but written in
                # their own loops below, so they are not counted here.
                children = [lambda: logic.write_pages_sitemap(press)]
                if press.active_news_items.exists():
                    children.append(lambda: logic.write_news_sitemap(press))

                logic.write_press_sitemap()
                _run(children)

            # Journal level
            for journal in journals:
                _log(f"Generating sitemap for {journal.name}")
                regular_issues = logic._journal_regular_issues(journal)
                issues_with_articles = [
                    i
                    for i in regular_issues
                    if logic._canonical_articles_for_issue(i).exists()
                ]
                has_orphans = logic._articles_not_in_any_regular_issue(journal).exists()
                has_news = journal.active_news_items.exists()

                # Sub-sitemaps written into the journal siteindex. Pages is
                # unconditional (Home and Accessibility are always canonicals),
                # so there is always at least one child.
                children = [lambda: logic.write_pages_sitemap(journal)]
                if has_news:
                    children.append(lambda: logic.write_news_sitemap(journal))
                children += [
                    (lambda issue=issue: logic.write_issue_sitemap(issue))
                    for issue in issues_with_articles
                ]
                if has_orphans:
                    children.append(
                        lambda: logic.write_not_in_any_issue_sitemap(journal)
                    )

                logic.write_journal_sitemap(journal)
                _run(children)

            # Repository level
            for repo in repositories:
                _log(f"Generating sitemap for {repo.name}")
                subjects = repo.subject_set.all()
                # Canonicalised list: each preprint counted under whichever
                # of its subjects sorts first by name, so subjects whose
                # preprints are all canonicalised elsewhere don't get an
                # empty sub-sitemap.
                subjects_with_preprints = [
                    s
                    for s in subjects
                    if logic._canonical_preprints_for_subject(s).exists()
                ]
                has_orphans = logic._preprints_without_subject(repo).exists()

                # Repos with no published preprints get no files at all.
                if not (subjects_with_preprints or has_orphans):
                    continue

                # Sub-sitemaps written into the repository siteindex.
                children = [lambda: logic.write_pages_sitemap(repo)]
                children += [
                    (lambda subject=subject: logic.write_subject_sitemap(subject))
                    for subject in subjects_with_preprints
                ]
                if has_orphans:
                    children.append(
                        lambda: logic.write_not_in_any_subject_sitemap(repo)
                    )

                logic.write_repository_sitemap(repo)
                _run(children)
