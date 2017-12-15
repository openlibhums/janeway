from django.core.management.base import BaseCommand

from identifiers import models as identifier_models


class Command(BaseCommand):
    """Takes a DOI and resolves the internal ID."""

    help = "Shows a native article ID from a DOI."

    def add_arguments(self, parser):
        """Adds arguments to Django's management command-line parser.

        :param parser: the parser to which the required arguments will be added
        :return: None
        """
        parser.add_argument('doi')

    def handle(self, *args, **options):
        """Shows a native system ID

        :param args: None
        :param options: Dictionary containing 'doi_suffix'
        :return: None
        """
        doi = options['doi']

        article = identifier_models.Identifier.objects.filter(id_type='doi', identifier=doi)[0].article

        print('Article ID is {0}'.format(article.id))
