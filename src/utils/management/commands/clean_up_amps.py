from re import sub
import sys

from django.conf import settings
from django.core.management.base import BaseCommand
from tqdm import tqdm

from submission.models import Article


class Command(BaseCommand):
    """
    Resaves articles that have lots of of escaped ampersands in their abstracts.
    These extra escaped ampersands are created by Python bleach when an ampersand
    is found inside an HTML comment. An earlier version of Janeway set
    BLEACH_STRIP_COMMENTS to False in global settings, but it is now True.
    So all we need to do is re-save the articles.
    """

    help = "Removes commented markup and long strings of ampersands from article abstracts."

    def handle(self, *args, **options):
        if not settings.BLEACH_STRIP_COMMENTS:
            self.stdout.write(self.style.ERROR(
                "BLEACH_STRIP_COMMENTS setting is not enabled"
            ))

        articles = Article.active_objects.filter(abstract__contains="&amp;amp;")
        for article in tqdm(articles):
            article.save()
            if article.abstract and "&amp;amp;" in article.abstract:
                tqdm.write(self.style.ERROR(
                    f"Failed to clean article: {article}"
                ))
