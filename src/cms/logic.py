__copyright__ = "Copyright 2023 Birkbeck, University of London"
__author__ = "Joseph Muller"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

import os

from django.shortcuts import reverse
from django.conf import settings

from journal import models as journal_models
from cms import models as models
from bs4 import BeautifulSoup
from core import models as core_models
from django.core.files.base import ContentFile
from comms import models as comms_models
from press import models as press_models
from utils.logger import get_logger

from lunr import lunr, get_default_builder
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
    to be used by lunr.js.
    """

    site_search_data = []
    for page in models.Page.objects.all():
        data = {}
        data['url'] = reverse('cms_page', kwargs={'page_name': page.name})
        data['name'] = page.display_name
        data['people'] = ''
        data['text'] = BeautifulSoup(page.content, 'html.parser').get_text()
        data['tags'] = ''
        site_search_data.append(data)

    for item in comms_models.NewsItem.active_objects.all():
        data = {}
        data['url'] = reverse('core_news_item', kwargs={'news_pk': item.pk})
        data['name'] = item.title
        data['people'] = item.byline()
        data['text'] = item.body
        if item.tags.count():
            data['tags'] = "Tags: " + ", ".join(
                [tag.text for tag in item.tags.all()]
            )
        else:
            data['tags'] = ''
        site_search_data.append(data)

    for journal in journal_models.Journal.objects.filter(
        hide_from_press=False
    ):
        data = {}
        data['url'] = journal.site_url()
        data['name'] = journal.name
        journal_contacts = core_models.Contacts.objects.filter(
            content_type__model='journal',
            object_id=journal.pk
        )
        data['people'] = '; '.join(
            [f'{c.name}, {c.role}' for c in journal_contacts]
        )
        data['text'] = journal.description_for_press
        data['tags'] = 'Disciplines: ' + ', '.join(
            [word.word for word in journal.keywords.all()]
        )
        site_search_data.append(data)

    press_contacts = core_models.Contacts.objects.filter(
        content_type__model='press',
    )
    data = {}
    data['url'] = '/contact'
    data['name'] = 'Contact'
    data['people'] = ''
    data['text'] = '; '.join([f'{c.name}, {c.role}' for c in press_contacts])
    data['tags'] = ''
    site_search_data.append(data)

    return site_search_data


def build_index():
    documents = get_press_site_search_data()
    builder = get_default_builder()
    builder.metadata_whitelist.append('position')
    return documents, lunr(
        ref='url',
        fields=('name', 'people', 'text', 'tags'),
        documents=documents,
        builder=builder,
    )


def update_index(press_id=1):
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
    index_filename = os.path.join(
        settings.SITE_SEARCH_DIR,
        f'_press_{ press.pk }_index.json'
    )
    index_file, created = models.MediaFile.objects.get_or_create(
        label=index_filename
    )
    if not created:
        index_file.unlink()

    documents, search_index = build_index()
    docs_json = json.dumps(documents)
    index_json = json.dumps(search_index.serialize())

    content_file = ContentFile(docs_json.encode('utf-8'))
    docs_file.file.save(docs_filename, content_file, save=True)

    content_file = ContentFile(index_json.encode('utf-8'))
    index_file.file.save(index_filename, content_file, save=True)
    return docs_file, index_file


def delete_index(press_id=1):
    press = press_models.Press.objects.get(pk=press_id)
    files_deleted = []
    paths = [
        os.path.join(
            SITE_SEARCH_PATH,
            f'_press_{ press.pk }_documents.json',
        ),
        os.path.join(
            SITE_SEARCH_PATH,
            f'_press_{ press.pk }_index.json',
        ),
    ]
    for path in paths:
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


def get_index_files(press):
    docs_filename = os.path.join(
        settings.SITE_SEARCH_DIR,
        f'_press_{ press.pk }_documents.json'
    )
    docs_file = models.MediaFile.objects.get(label=docs_filename)
    index_filename = os.path.join(
        settings.SITE_SEARCH_DIR,
        f'_press_{ press.pk }_index.json'
    )
    index_file = models.MediaFile.objects.get(label=index_filename)
    return docs_file, index_file
