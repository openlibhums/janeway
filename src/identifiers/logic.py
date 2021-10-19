__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


import datetime
from uuid import uuid4
import requests
from bs4 import BeautifulSoup

from django.urls import reverse
from django.template.loader import render_to_string
from django.utils.http import urlencode
from django.utils.html import strip_tags
from django.conf import settings
from django.contrib import messages
from django.utils import timezone

import sys
from utils import models as util_models
from utils.function_cache import cache
from utils.logger import get_logger
from crossref.restful import Depositor
from identifiers import models

logger = get_logger(__name__)


def register_crossref_doi(identifier):
    from utils import setting_handler

    domain = identifier.article.journal.domain
    pingback_url = urlencode({'pingback': 'http://{0}{1}'.format(domain, reverse('crossref_pingback'))})

    use_crossref = setting_handler.get_setting('Identifiers', 'use_crossref',
                                               identifier.article.journal).processed_value

    if not use_crossref:
        logger.info("[DOI] Not using Crossref DOIs on this journal. Aborting registration.")
        return 'Crossref Disabled', 'Disabled'

    test_mode = setting_handler.get_setting(
            'Identifiers', 'crossref_test', identifier.article.journal
    ).processed_value or settings.DEBUG

    if test_mode:
        util_models.LogEntry.add_entry('Submission', "DOI registration running in test mode", 'Info',
                                       target=identifier.article)
    else:
        util_models.LogEntry.add_entry('Submission', "DOI registration running in live mode", 'Info',
                                       target=identifier.article)

    return send_crossref_deposit(test_mode, identifier)


def register_crossref_component(article, xml, supp_file):
    from utils import setting_handler

    use_crossref = setting_handler.get_setting('Identifiers', 'use_crossref',
                                               article.journal).processed_value

    if not use_crossref:
        logger.info("[DOI] Not using Crossref DOIs on this journal. Aborting registration.")
        return

    test_mode = setting_handler.get_setting(
            'Identifiers', 'crossref_test', article.journal
    ).processed_value or settings.DEBUG

    if test_mode:
        util_models.LogEntry.add_entry('Submission', "DOI component registration running in test mode", 'Info',
                                       target=article)
    else:
        util_models.LogEntry.add_entry('Submission', "DOI component registration running in live mode", 'Info',
                                       target=article)

    doi_prefix = setting_handler.get_setting('Identifiers', 'crossref_prefix', article.journal)
    username = setting_handler.get_setting('Identifiers', 'crossref_username', article.journal).processed_value
    password = setting_handler.get_setting('Identifiers', 'crossref_password', article.journal).processed_value

    depositor = Depositor(prefix=doi_prefix, api_user=username, api_key=password, use_test_server=test_mode)
    response = depositor.register_doi(submission_id='component{0}.xml'.format(uuid4()), request_xml=xml)

    logger.debug("[CROSSREF:DEPOSIT:{0}] Sending".format(article.id))
    logger.debug("[CROSSREF:DEPOSIT:%s] Response code %s" % (article.id, response.status_code))

    if response.status_code != 200:
        util_models.LogEntry.add_entry('Error',
                                       "Error depositing: {0}. {1}".format(response.status_code, response.text),
                                       'Debug',
                                       target=article)

        status = "Error depositing: {code}, {text}".format(
            code=response.status_code,
            text=response.text
        )
        logger.error(status)
        logger.error(response.text)
        error = True
    else:
        util_models.LogEntry.add_entry('Submission', "Deposited DOI.", 'Info', target=article)


def create_crossref_context(identifier):
    timestamp_suffix = identifier.article.journal.get_setting(
        'crossref',
        'crossref_date_suffix',
    )

    from utils import setting_handler
    template_context = {
        'batch_id': uuid4(),
        'timestamp': int(round((datetime.datetime.now() - datetime.datetime(1970, 1, 1)).total_seconds())),
        'depositor_name': setting_handler.get_setting('Identifiers', 'crossref_name',
                                                      identifier.article.journal).processed_value,
        'depositor_email': setting_handler.get_setting('Identifiers', 'crossref_email',
                                                       identifier.article.journal).processed_value,
        'registrant': setting_handler.get_setting('Identifiers', 'crossref_registrant',
                                                  identifier.article.journal).processed_value,
        'journal_title': (
                identifier.article.publication_title
                or identifier.article.journal.name
        ),
        'abstract': strip_tags(identifier.article.abstract or ''),
        'journal_issn': identifier.article.journal.issn,
        'print_issn': identifier.article.journal.print_issn or None,
        'date_published': identifier.article.date_published,
        'date_accepted': identifier.article.date_accepted,
        'pages': identifier.article.page_numbers,
        'issue': identifier.article.issue,
        'article_title': '{0}{1}{2}'.format(
            identifier.article.title,
            ' ' if identifier.article.subtitle is not None else '',
            identifier.article.subtitle if identifier.article.subtitle is not None else ''),
        'authors': identifier.article.frozenauthor_set.all(),
        'doi': identifier.identifier,
        'article_url': identifier.article.url,
        'now': timezone.now(),
        'timestamp_suffix': timestamp_suffix,
    }

    # append citations for i4oc compatibility
    template_context["citation_list"] = extract_citations_for_crossref(
        identifier.article)

    # append PDFs for similarity check compatibility
    pdfs = identifier.article.pdfs
    if len(pdfs) > 0:
        template_context['pdf_url'] = identifier.article.pdf_url

    if identifier.article.license:
        template_context["license"] = identifier.article.license.url

    return template_context


def extract_citations_for_crossref(article):
    """ Extracts the citations in a format compatible for crossref deposits

    It can only handle articles with an XML galley using a DTD
    compatible with the XSL provided by crossref themselves
    :param Article: A submission.models.Article instance
    :return: The formatted string containing the references
    """
    render_galley = article.get_render_galley
    citations = None
    if render_galley and render_galley.type == 'xml':
        try:
            logger.debug('Doing crossref citation list transform:')
            xml_transformed = render_galley.render_crossref()
            logger.debug(xml_transformed)

            # extract the citation list
            souped_xml = BeautifulSoup(str(xml_transformed), 'lxml')
            citation_list = souped_xml.find('citation_list')

            # Crossref only accepts DOIs on identifier format (not url)
            url_element = "doi.org/"
            for doi in citation_list.findAll("doi"):
                if doi.string and url_element in doi.string:
                    *_, doi.string = doi.string.split(url_element)

            if citation_list:
                citations = str(citation_list.extract())
                citations = citations.replace(
                    "<cyear", "<cYear"
                ).replace(
                    "</cyear", "</cYear"
                )
        except Exception as e:
            logger.error('Error transforming Crossref citations: %s' % e)
    else:
        logger.debug('No XML galleys found for crossref citation extraction')

    return citations


def get_crossref_template(item):
    if item.journal.is_conference:
        return 'common/identifiers/crossref_conference.xml'
    else:
        return 'common/identifiers/crossref_article.xml'


def send_crossref_deposit(test_mode, identifier):
    # todo: work out whether this is acceptance or publication
    # if it's acceptance, then we use "0" for volume and issue
    # if publication, then use real values
    # the code here is for acceptance

    from utils import setting_handler
    article = identifier.article
    error = False

    template = get_crossref_template(article)
    template_context = create_crossref_context(identifier)
    rendered = render_to_string(template, template_context)

    logger.debug(rendered)

    util_models.LogEntry.add_entry('Submission', "Sending request: {0}".format(rendered),
                                   'Info',
                                   target=identifier.article)
    doi_prefix = setting_handler.get_setting('Identifiers', 'crossref_prefix', article.journal)
    username = setting_handler.get_setting('Identifiers', 'crossref_username', identifier.article.journal).processed_value
    password = setting_handler.get_setting('Identifiers', 'crossref_password',
                                           identifier.article.journal).processed_value

    filename = uuid4()

    depositor = Depositor(prefix=doi_prefix, api_user=username, api_key=password, use_test_server=test_mode)

    try:
        response = depositor.register_doi(submission_id=filename, request_xml=rendered)
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
        status = 'Error depositing. Could not connect to Crossref ({0}). Error: {1}'.format(
            depositor.get_endpoint(verb='deposit'),
            e,
        )
        util_models.LogEntry.add_entry(
            'Error',
            status,
            'Debug',
            target=identifier.article,
        )
        logger.error(status)
        return status, error

    logger.debug("[CROSSREF:DEPOSIT:{0}] Sending".format(identifier.article.id))
    logger.debug("[CROSSREF:DEPOSIT:%s] Response code %s" % (identifier.article.id, response.status_code))

    if response.status_code != 200:
        util_models.LogEntry.add_entry('Error',
                                       "Error depositing: {0}. {1}".format(response.status_code, response.text),
                                       'Debug',
                                       target=identifier.article)

        status = "Error depositing: {code}, {text}".format(
            code=response.status_code,
            text=response.text
        )
        logger.error(status)
        error = True
    else:
        status = "Deposited DOI"
        util_models.LogEntry.add_entry('Submission', status, 'Info', target=identifier.article)
        logger.info(status)

        crd = models.CrossrefDeposit(identifier=identifier, file_name=filename)
        crd.save()

        crd.poll()

    return status, error


def create_crossref_doi_identifier(article, doi_suffix=None, suffix_is_whole_doi=False):
    """ Creates (but does not register remotely) a Crossref DOI

    :param article: the article for which to create the DOI
    :param doi_suffix: an optional DOI suffix
    :return:
    """

    from utils import setting_handler

    if doi_suffix is None:
        doi_suffix = article.id

    if not suffix_is_whole_doi:
        doi_prefix = setting_handler.get_setting('Identifiers', 'crossref_prefix', article.journal)
        doi = '{0}/{1}'.format(doi_prefix, doi_suffix)
    else:
        doi = doi_suffix

    doi_options = {
        'id_type': 'doi',
        'identifier': doi,
        'article': article
    }

    from identifiers import models as identifier_models

    return identifier_models.Identifier.objects.create(**doi_options)


def generate_crossref_doi_with_pattern(article):
    """
    Creates a crossref doi utilising a preset pattern.
    :param article: article objects
    :return: returns a DOI
    """

    from utils import setting_handler, render_template

    doi_prefix = setting_handler.get_setting('Identifiers', 'crossref_prefix', article.journal).value
    doi_suffix = render_template.get_requestless_content({'article': article},
                                                         article.journal,
                                                         'doi_pattern',
                                                         group_name='Identifiers')

    doi_options = {
        'id_type': 'doi',
        'identifier': '{0}/{1}'.format(doi_prefix, doi_suffix),
        'article': article
    }

    from identifiers import models as identifier_models

    return identifier_models.Identifier.objects.create(**doi_options)


@cache(600)
def render_doi_from_pattern(article):
    from utils import setting_handler, render_template

    doi_prefix = setting_handler.get_setting('Identifiers', 'crossref_prefix', article.journal).value
    doi_suffix = render_template.get_requestless_content({'article': article},
                                                         article.journal,
                                                         'doi_pattern',
                                                         group_name='Identifiers')

    return '{0}/{1}'.format(doi_prefix, doi_suffix)


def get_preprint_tempate_context(request, identifier):
    article = identifier.article

    template_context = {
        'batch_id': uuid4(),
        'timestamp': int(round((datetime.datetime.now() - datetime.datetime(1970, 1, 1)).total_seconds())),
        'depositor_name': request.press.name,
        'depositor_email': request.press.main_contact,
        'registrant': request.press.name,
        'journal_title': request.press.name,
        'journal_issn': '',
        'journal_month': identifier.article.date_published.month,
        'journal_day': identifier.article.date_published.day,
        'journal_year': identifier.article.date_published.year,
        'journal_volume': 0,
        'journal_issue': 0,
        'article_title': '{0}{1}{2}'.format(
            identifier.article.title,
            ' ' if identifier.article.subtitle is not None else '',
            identifier.article.subtitle if identifier.article.subtitle is not None else ''),
        'authors': identifier.article.authors.all(),
        'article_month': identifier.article.date_published.month,
        'article_day': identifier.article.date_published.day,
        'article_year': identifier.article.date_published.year,
        'doi': identifier.identifier,
        'article_url': reverse('preprints_article', kwargs={'article_id': article.pk}),
    }

    return template_context


def register_preprint_doi(request, crossref_enabled, identifier):
    """
    Registers a preprint doi with crossref, has its own function as preprints dont have things like issues.
    :param identifier: Identifier object
    :return: Nothing
    """

    if not crossref_enabled:
        messages.add_message(request, messages.WARNING, 'Crossref DOIs are not enabled for this preprint service.')
    else:

        # Set the URL for depositing based on whether we are in test mode
        if request.press.get_setting_value('Crossref Test Mode') == 'On':
            url = CROSSREF_TEST_URL
        else:
            url = CROSSREF_LIVE_URL

        template_context = get_preprint_tempate_context(request, identifier)
        template = 'common/identifiers/crossref.xml'
        rendered = render_to_string(template, template_context)

        pdfs = identifier.article.pdfs
        if len(pdfs) > 0:
            template_context['pdf_url'] = identifier.article.pdf_url

        response = requests.post(url, data=rendered.encode('utf-8'),
                                 auth=(request.press.get_setting_value("Crossref Login"),
                                       request.press.get_setting_value("Crossref Password")),
                                 headers={"Content-Type": "application/vnd.crossref.deposit+xml"})

        if response.status_code != 200:
            util_models.LogEntry.add_entry('Error',
                                           "Error depositing: {0}. {1}".format(response.status_code, response.text),
                                           'Debug',
                                           target=identifier.article)
            logger.error("Error depositing: {}".format(response.status_code))
            logger.error(response.text)
        else:
            token = response.json()['message']['batch-id']
            status = response.json()['message']['status']
            util_models.LogEntry.add_entry('Submission', "Deposited {0}. Status: {1}".format(token, status), 'Info',
                                           target=identifier.article)
            logger.info("Status of {} in {}: {}".format(token, identifier.identifier, status))
