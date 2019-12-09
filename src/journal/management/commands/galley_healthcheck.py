import requests
from bs4 import BeautifulSoup

from django.core.management.base import BaseCommand

from journal import models as journal_models
from submission import models
from core.templatetags.files import has_missing_supplements


class Command(BaseCommand):
    """Checks the health of all the published article galleys"""

    help = "Checks the health of all the published article galleys"

    def add_arguments(self, parser):
        parser.add_argument('journal_codes', nargs='*', default=None)

    def handle(self, *args, **options):
        """ Healthchecks of all article galleys in two ways
        1. Verifies all published articles have a PDF or a render galley
        2. Verifies that all the images are available for each render galley

        :param args: None
        :param options: None
        :return: None
        """
        journal_codes = options.get('journal_codes')

        journals = journal_models.Journal.objects.all()
        if journal_codes:
            journals = journals.filter(code__in=journal_codes)

        for journal in journals:
            articles = models.Article.objects.filter(
                    stage=models.STAGE_PUBLISHED, journal=journal)

            for article in articles:
                print("Verifying {article.pk} - {article.title}".format(article=article))
                render_galley = article.get_render_galley
                has_pdf = article.pdfs.exists()
                if not (has_pdf or render_galley):
                    print("[{}] has no galleys".format(article.pk))
                elif render_galley:
                    images_url = retrieve_image_urls_from_galley(render_galley)
                    for url in images_url:
                        response = requests.get(journal.site_url(path=url))
                        if not response.ok or not len(response.content):
                            print("[{}][MISSING IMAGE][{}]".format(article.pk, url))


def retrieve_image_urls_from_galley(galley):
    xml_file_contents = galley.file.get_file(galley.article)

    souped_xml = BeautifulSoup(xml_file_contents, 'lxml')

    elements = {
        'img': 'src',
        'graphic': 'xlink:href'
    }

    return [
        val.get(attribute)
        for element, attribute in elements.items()
        for idx, val in enumerate(souped_xml.findAll(element))
        if val.get(attribute)
    ]
