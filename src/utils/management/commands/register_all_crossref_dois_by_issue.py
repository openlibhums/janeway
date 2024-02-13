from django.core.management.base import BaseCommand

from journal import models
from identifiers import logic


class Command(BaseCommand):
    """Takes an OAI PMH url and pulls information into Janeway."""

    help = "Registers a DOI with Crossref."

    def add_arguments(self, parser):
        """Adds arguments to Django's management command-line parser.

        :param parser: the parser to which the required arguments will be added
        :return: None
        """
        parser.add_argument('--journal_code')
        parser.add_argument(
            '-d',
            '--dry_run',
            action="store_true",
            default=False,
        )

    def handle(self, *args, **options):
        """Calls the Crossref registration options

        :param args: None
        :param options: Dictionary containing 'article_id'
        :return: None
        """
        journal = models.Journal.objects.get(code=options.get('journal_code'))
        dry_run = options.get('dry_run')
        test_enabled = journal.get_setting(
            'Identifiers',
            'crossref_test',
        )
        if dry_run:
            print(
                'Dry run:'
            )
        print(
            "Running in Crossref {}".format(
                'Test' if test_enabled else 'Live',
            )
        )

        for issue in journal.published_issues:
            articles_to_deposit = []
            for article in issue.article_set.all():
                if article.journal:
                    articles_to_deposit.append(article)

            print(
                f"Depositing {len(articles_to_deposit)} articles in {issue.display_title}."
            )
            if not dry_run and articles_to_deposit:
                logic.register_batch_of_crossref_dois(
                    articles_to_deposit,
                    **{},
                )

