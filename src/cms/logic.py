__copyright__ = "Copyright 2023 Birkbeck, University of London"
__author__ = "Joseph Muller"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

import os
import time
import requests
from urllib.parse import urlparse, urljoin

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from journal import models as journal_models
from repository import models as repository_models
from cms import models as models
from bs4 import BeautifulSoup, Tag
from django.core.files.base import ContentFile
from press import models as press_models
from utils.logger import get_logger

import json

logger = get_logger(__name__)


SITE_SEARCH_PATH = os.path.join(
    settings.MEDIA_ROOT,
    'press',
    settings.SITE_SEARCH_DIR,
)


def get_press_site_search_data():
    """
    Generates data for press-level site search index
    to be used by MiniSearch
    """

    documents = []
    indexed_urls = []
    page_ids = {1}
    press = press_models.Press.objects.first()
    base = f'http://{press.domain}'
    exclude_urls = [
        journal.site_url() for journal in journal_models.Journal.objects.all()
    ] + [
        repo.site_url() for repo in repository_models.Repository.objects.all()
    ]

    def add_page(url):
        time.sleep(.25)
        try:
            response = requests.get(url)
            indexed_urls.append(url)
        except requests.exceptions.ConnectionError:
            logger.warn('Please run server to index site search')
            return

        if response.status_code != 200:
            return

        html = BeautifulSoup(response.text, 'html.parser')
        body = html.find('body')
        if not isinstance(body, Tag):
            return

        try:
            name = html.find('h1').get_text().strip()
        except AttributeError:
            name = html.title.get_text().strip()

        for non_content_selector in ['script', '.djdt-hidden']:
            for element in body.select(non_content_selector):
                element.decompose()

        for anchor in html.find_all('a'):
            try:
                path = anchor['href'].strip()
            except KeyError:
                continue
            while path.startswith('//'):
                path = path[1:]
            path = path.split('#')[0]
            deeper_url = urljoin(url, path)

            exclude = False
            for exclude_url in exclude_urls:
                if exclude_url in deeper_url:
                    exclude = True
            for indexed_url in indexed_urls:
                if deeper_url + '/' == indexed_url:
                    exclude = True
                if deeper_url == indexed_url + '/':
                    exclude = True
            if (
                not exclude
            ) and (
                urlparse(deeper_url).netloc == urlparse(url).netloc
            ) and (
                not path.startswith('#')
            ) and (
                deeper_url not in indexed_urls
            ):
                add_page(deeper_url)

        for non_content_selector in ['header', 'footer', 'h1']:
            for element in body.select(non_content_selector):
                element.decompose()

        data = {}
        page_id = max(page_ids) + 1
        data['id'] = page_id
        page_ids.add(page_id)
        data['url'] = url
        data['name'] = name
        data['text'] = body.get_text()
        documents.append(data)

    path = '/'
    url = urljoin(base, path)
    add_page(url)

    if not len(documents) > 0:
        logger.error('Search data store is empty')

    return documents


def update_search_data(press_id=1):
    press = press_models.Press.objects.get(pk=press_id)
    docs_filename = os.path.join(
        settings.SITE_SEARCH_DIR,
        f'_press_{ press.pk }_documents.json'
    )
    docs_file, created = models.MediaFile.objects.get_or_create(
        label=docs_filename
    )
    if not created:
        docs_file.unlink()

    documents = get_press_site_search_data()
    docs_json = json.dumps(documents)

    content_file = ContentFile(docs_json.encode('utf-8'))
    docs_file.file.save(docs_filename, content_file, save=True)
    return docs_file


def delete_search_data(press_id=1):
    press = press_models.Press.objects.get(pk=press_id)
    files_deleted = []
    path = os.path.join(
        SITE_SEARCH_PATH,
        f'_press_{ press.pk }_documents.json',
    )
    if os.path.exists(path):
        os.unlink(path)
        files_deleted.append(path)
    if settings.IN_TEST_RUNNER:
        if os.listdir(SITE_SEARCH_PATH):
            logger.warning(
                f'Left-over test files: {os.listdir(SITE_SEARCH_PATH)}'
            )
        else:
            os.rmdir(SITE_SEARCH_PATH)

    return files_deleted


def get_search_data_file(press):
    docs_filename = os.path.join(
        settings.SITE_SEARCH_DIR,
        f'_press_{ press.pk }_documents.json'
    )
    try:
        docs_file = models.MediaFile.objects.get(label=docs_filename)
    except models.MediaFile.DoesNotExist:
        raise ImproperlyConfigured(
            'Site search indexing is turned on, but there is no data file. '
            'Set settings.SITE_SEARCH_INDEXING_FREQUENCY to None to turn off, '
            'or run manage.py generate_site_search_data.'
        )
    return docs_file
