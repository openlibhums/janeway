import time

from django.core.management.base import BaseCommand

from identifiers import logic as identifier_logic
from submission import models as submission_models
from journal import models as journal_models


class Command(BaseCommand):
    """Takes an OAI PMH url and pulls information into Janeway."""

    help = "Registers all article DOIs with Crossref."

    def add_arguments(self, parser):
        """Adds arguments to Django's management command-line parser.

        :param parser: the parser to which the required arguments will be added
        :return: None
        """
        parser.add_argument('journal_code')

    def handle(self, *args, **options):
        """Calls the Crossref registration options

        :param args: None
        :param options: Dictionary containing 'journal_code'
        :return: None
        """
        journal = journal_models.Journal.objects.get(
            code=options.get('journal_code'),
        )
        articles = submission_models.Article.objects.filter(
            journal=journal,
            date_published__isnull=False,
        )

        for article in articles:
            print('Handling article {0}'.format(article.pk))
            if article.is_published:
                print('Article is published')
                try:
                    identifier = article.get_identifier('doi', object=True)

                    if identifier and identifier.is_doi:
                        identifier.register()
                    else:
                        identifier = identifier_logic.generate_crossref_doi_with_pattern(article)
                        identifier.register()
                except AttributeError as e:
                    print('Error {0}'.format(e))

            else:
                print('Article {} is not published.'.format(article.pk))

            time.sleep(1)
