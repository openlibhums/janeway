from django.core.management.base import BaseCommand

from submission import models


class Command(BaseCommand):

    help = "Used locally for whatever I want."

    def handle(self, *args, **options):
        article = models.Article.objects.get(pk=4426)

        article.best_last_modified_date()