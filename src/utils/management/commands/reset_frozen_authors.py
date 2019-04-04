from django.core.management.base import BaseCommand

from submission import models as submission_models


class Command(BaseCommand):
    """ A management command to reset frozen author records with live profile records."""

    help = "Resets frozen author records with fresh data."

    def add_arguments(self, parser):
        """Adds arguments to Django's management command-line parser.

        :param parser: the parser to which the required arguments will be added
        :return: None
        """
        parser.add_argument("--hard",
                action='store_true',
                default=False,
                help="Also deletes manually added frozen records"
        )

    def handle(self, *args, **options):
        """ Resets frozen author records with live profile records.

        :param args: None
        :param options: None.
        :return: None
        """
        filters = {}
        if options["hard"] is True:
            filters["author__isnull"] = True

        articles = submission_models.Article.objects.all()
        submission_models.FrozenAuthor.objects.filter(**filters).delete()

        for article in articles:
            for author in article.authors.all():

                frozen_dict = {
                    'article': article,
                    'author': author,
                    'first_name': author.first_name,
                    'middle_name': author.middle_name,
                    'last_name': author.last_name,
                    'institution': author.institution,
                    'department': author.department,
                }

                frozen_author = submission_models.FrozenAuthor.objects.create(**frozen_dict)

                author.frozen_author = frozen_author
                author.save()
