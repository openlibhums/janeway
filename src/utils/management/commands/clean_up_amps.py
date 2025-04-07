from submission.models import Article
from re import sub
from tqdm import tqdm

from django.core.management.base import BaseCommand


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
        articles = Article.active_objects.filter(abstract__contains="&amp;amp;")
        for article in tqdm(articles):
            article.save()
