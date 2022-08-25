import uuid
import os
import shutil
import codecs
from mock import Mock

from django.conf import settings
from django.template.loader import render_to_string
from django.http import HttpRequest

from core import files


def prepare_temp_folder(request=None, issue=None, article=None, loc_code=None):
    """
    Perpares a temp folder to store files for zipping
    :param request: Request object
    :param issue: Issue Object
    :param article: Article object
    :param loc_code: string
    :return: Folder path, string
    """
    folder_string = str(uuid.uuid4())

    if article and issue and request:
        folder_string = '{journal_code}_{vol}_{issue}_{pk}'.format(
            journal_code=request.journal.code,
            vol=issue.volume,
            issue=issue.issue,
            pk=article.pk)
    elif issue and request:
        folder_string = '{journal_code}_{vol}_{issue}_{year}'.format(
            journal_code=request.journal.code,
            vol=issue.volume,
            issue=issue.issue,
            year=issue.date.year)
    elif loc_code:
        folder_string = loc_code

    folder = os.path.join(settings.BASE_DIR, 'files', 'temp', 'deposit', folder_string)
    files.mkdirs(folder)

    return folder, folder_string


def zip_temp_folder(temp_folder):
    shutil.make_archive(temp_folder, 'zip', temp_folder)
    shutil.rmtree(temp_folder)


def get_best_deposit_xml_galley(article, galleys):
    xml_galleys = galleys.filter(
        file__mime_type__in=files.XML_MIMETYPES,
        public=True,
    ).order_by('-file__date_uploaded')

    if article.render_galley:
        return article.render_galley

    if xml_galleys:
        try:
            return xml_galleys.filter(public=True)[0]
        except IndexError:
            pass
        return xml_galleys.first()
    return None


def get_best_deposit_pdf_galley(galleys):
    pdf_galley = galleys.filter(
        file__mime_type__in=files.PDF_MIMETYPES,
        public=True,
    ).order_by('-file__date_uploaded').first()

    return pdf_galley


def get_best_deposit_html_galley(galleys):
    html_galley = galleys.filter(
        file__mime_type__in=files.HTML_MIMETYPES,
        public=True,
    ).order_by('-file__date_uploaded').first()

    return html_galley


def generate_jats_metadata(article, article_folder, command_line=True):
    if command_line:
        print('Generating JATS file...')
    template = 'portico/jats.xml'
    context = {
        'article': article,
        'journal': article.journal
    }

    rendered_jats = render_to_string(template, context)
    file_name = '{id}.xml'.format(id=article.pk)
    full_path = os.path.join(article_folder, file_name)

    with codecs.open(full_path, 'w', "utf-8") as file:
        file.write(rendered_jats)
        file.close()


def create_fake_request(issue=None):
    request = Mock(HttpRequest)
    request.GET = Mock()
    request.journal = issue.journal
    if issue:
        request.POST = {'export-issue': issue.pk}

    return request


def file_path(article_id, uuid_filename):
    return os.path.join(
        settings.BASE_DIR,
        'files',
        'articles',
        str(article_id),
        str(uuid_filename),
    )
