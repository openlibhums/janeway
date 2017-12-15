from django.core.management.base import BaseCommand

from identifiers import logic as identifier_logic
from submission import models as submission_models


class Command(BaseCommand):
    """Takes an OAI PMH url and pulls information into Janeway."""

    help = "Registers a DOI with Crossref."

    def add_arguments(self, parser):
        """Adds arguments to Django's management command-line parser.

        :param parser: the parser to which the required arguments will be added
        :return: None
        """
        parser.add_argument('article_id')

    def handle(self, *args, **options):
        """Calls the Crossref registration options

        :param args: None
        :param options: Dictionary containing 'article_id'
        :return: None
        """
        article = submission_models.Article.objects.get(pk=options['article_id'])

        identifier = article.get_identifier('doi', object=True)

        if identifier.is_doi:
            identifier.register()
        else:
            identifier = identifier_logic.generate_crossref_doi_with_pattern(article)
            identifier.register()
