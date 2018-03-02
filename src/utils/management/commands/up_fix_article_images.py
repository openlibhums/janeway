import requests
from bs4 import BeautifulSoup
import re

from django.core.management.base import BaseCommand

from journal import models as journal_models
from submission import models
from core.templatetags.files import has_missing_supplements
from core import files, models as core_models


class Command(BaseCommand):
    """Fixes bad import of XML related image files."""

    help = "Fixes bad import of XML related image files."

    def add_arguments(self, parser):
        """ Adds arguments to Django's management command-line parser.

        :param parser: the parser to which the required arguments will be added
        :return: None
        """
        parser.add_argument('journal_code', nargs='?', default=None)
        parser.add_argument('url')

    def handle(self, *args, **options):
        """Loops through a journals articles, finds its XML and files and then pulls full versions from UP's site.

        :param args: None
        :param options: None
        :return: None
        """
        journal_code = options.get('journal_code', None)
        base_url = options.get('url')
        journal = None

        try:
            journal = journal_models.Journal.objects.get(code=journal_code)
        except journal_models.Journal.DoesNotExist:
            print('No journal with that code found.')

        if journal:
            articles = models.Article.objects.filter(stage=models.STAGE_PUBLISHED, journal=journal)

            for article in articles:
                for galley in article.galley_set.all():
                    if galley.label == 'XML' or galley.file.mime_type == 'application/xml' or galley.file.mime_type == 'text/xml':
                        missing_supplements = has_missing_supplements(galley)

                        if missing_supplements:
                            url = '{url}/articles/{doi}'.format(url=base_url, doi=galley.article.identifier.identifier)
                            r = requests.get(url)
                            soup = BeautifulSoup(r.text, 'lxml')
                            main_article = soup.find('div', {'class': 'major-article-block'})
                            images = main_article.findAll('img')

                            galley_content = files.get_file(galley.file, article)
                            galley_soup = BeautifulSoup(galley_content, 'lxml')
                            galley_images = galley_soup.findAll('graphic')

                            galley_hrefs = [image.get('xlink:href') for image in galley_images]

                            print(url)

                            loop_counter = 0
                            for img in images:
                                img_url = '{url}/{img_src}'.format(url=url, img_src=img['src'])
                                href = galley_hrefs[loop_counter]
                                href_ids = re.findall('(\\d+)', href)
                                file_id = href_ids[1]

                                file = core_models.File.objects.get(id=file_id)
                                file.privacy = 'public'
                                file.save()
                                file.unlink_file(article.journal)

                                try:
                                    image_r = requests.get(img_url, stream=True)
                                    if image_r.status_code == 200:
                                        with open(file.self_article_path(), 'wb+') as f:
                                            for chunk in r.iter_content(1024):
                                                f.write(chunk)
                                except FileNotFoundError:
                                    print('File not found in files directory.')

                                loop_counter += 1
