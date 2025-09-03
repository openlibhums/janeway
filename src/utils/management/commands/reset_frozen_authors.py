import warnings

from django.core.management.base import BaseCommand

from submission import models as submission_models


class Command(BaseCommand):
    """A management command to reset frozen author records with live profile records."""

    help = "Resets frozen author records with fresh data."

    def add_arguments(self, parser):
        """Adds arguments to Django's management command-line parser.

        :param parser: the parser to which the required arguments will be added
        :return: None
        """
        parser.add_argument(
            "--hard",
            action="store_true",
            default=False,
            help="Also deletes manually added frozen records",
        )

    def handle(self, *args, **options):
        """Resets frozen author records with live profile records.

        :param args: None
        :param options: None.
        :return: None
        """
        warnings.warn(
            "This command can cause unintended behavior because "
            "accounts are not created for all authors during submission."
        )
        filters = {}
        if options["hard"] is True:
            filters["author__isnull"] = True
        else:
            filters["author__isnull"] = False

        articles = submission_models.Article.objects.all()

        for article in articles:
            for fa in article.frozenauthor_set.filter(**filters):
                author = fa.author
                fa.delete()
                if author:
                    author.snapshot_as_author(article)
