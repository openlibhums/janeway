import requests
from bs4 import BeautifulSoup

from django.core.management.base import BaseCommand

from utils import setting_handler
from journal import models as jm
from submission import models as sm
from metrics import models


def process_article(link, article):
    print('Processing article', end='...')
    doi = link.doi.contents[0]

    defaults = {
        'year': link.year.contents[0],
        'journal_title': link.journal_title.contents[0],
        'article_title': link.article_title.contents[0],
    }

    print(defaults)

    models.ArticleLink.objects.get_or_create(
        article=article,
        doi=doi,
        object_type='article',
    )
    print('[ok]')


def process_book(link, article):
    print('Processing book', end='...')

    print('[ok]')


class Command(BaseCommand):
    """
    Pulls forward links from Crossref.
    """

    help = "Pulls forward links and creates altmetrics."

    def add_arguments(self, parser):
        """ Adds arguments to Django's management command-line parser.

        :param parser: the parser to which the required arguments will be added
        :return: None
        """
        parser.add_argument('journal_code')
        parser.add_argument('date', default='2000-01-01', nargs='?')

    def handle(self, *args, **options):
        """Pulls forward links

        :param args: None
        :param options: None
        :return: None
        """
        date = options.get('date', '2000-01-01')
        journal_code = options.get('journal_code')

        journal = jm.Journal.objects.get(code=journal_code)
        usr = setting_handler.get_setting(
            'Identifiers',
            'crossref_username',
            journal,
        ).value
        pwd = setting_handler.get_setting(
            'Identifiers',
            'crossref_password',
            journal,
        ).value
        doi = setting_handler.get_setting(
            'Identifiers',
            'crossref_prefix',
            journal,
        ).value

        url = 'https://doi.crossref.org/servlet/getForwardLinks?usr={usr}&pwd={pwd}&doi={doi}&startDate={date}'.format(
            usr=usr,
            pwd=pwd,
            doi=doi,
            date=date
        )

        print('Making request.', end='... ')
        r = requests.get(url)
        print('[ok]')

        print('Souping response', end='... ')
        soup = BeautifulSoup(r.text, 'lxml')
        print('[ok]')

        print('Finding forward links', end='...')
        forward_links = soup.find_all('forward_link')
        print('[ok]')

        print('Looping through links', end='...')
        for link in forward_links:
            type = link.doi.get('type')
            doi = link.get('doi')

            article = sm.Article.get_article(
                journal,
                'doi',
                doi,
            )

            if article:
                if type == 'journal_article':
                    process_article(link, article)
                else:
                    process_book(link, article)
            else:
                print('Article not found.')

        print(len(forward_links))
