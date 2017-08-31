import feedparser
from urllib.parse import urlparse

from django.core.management.base import BaseCommand
from django.urls import reverse

from comms import models as comms_models


class Command(BaseCommand):
    """
    A management command that removes duplicate named settings in the core.Setting model. This is useful when you have
    corrupted the settings table by running early dev versions of Janeway.
    """

    help = "Deletes duplicate settings."

    def handle(self, *args, **options):
        """Delete duplicate named settings in the core.Setting model.

        :param args: None
        :param options: None
        :return: None
        """
        paged = 1

        while True:
            d = feedparser.parse('https://about.openlibhums.org/feed/?paged=%s' % paged)

            for item in d['entries']:
                try:
                    news_item = comms_models.NewsItem.objects.get(title=item['title'])
                    if news_item:
                        reversal = reverse('core_news_item', kwargs={'news_pk': news_item.pk})
                        url_path = urlparse(item['link']).path

                        print("Redirect 301 {0} {1}".format(url_path, reversal))
                except BaseException as e:
                    print(e)

            break
            paged = paged + 1
