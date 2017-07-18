from django.core.management.base import BaseCommand

from submission import models as submission_models


class Command(BaseCommand):
    """ A management command to reset frozen author records with live profile records."""

    help = "Resets frozen author records with fresh data."

    def handle(self, *args, **options):
        """ Resets all frozen author records with live profile records.

        :param args: None
        :param options: None.
        :return: None
        """

        articles = submission_models.Article.objects.all()
        submission_models.FrozenAuthor.objects.all().delete()

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
