__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


import datetime
from uuid import uuid4
import requests

from django.urls import reverse
from django.template.loader import render_to_string
from django.utils.http import urlencode
from django.contrib import messages
from django.utils import timezone

import sys
from utils import models as util_models
from utils.function_cache import cache
from utils.logger import get_logger

logger = get_logger(__name__)

CROSSREF_TEST_URL = 'https://api.crossref.org/deposits?test=true'
CROSSREF_LIVE_URL = 'https://api.crossref.org/deposits'


def register_crossref_doi(identifier):
    from utils import setting_handler

    domain = identifier.article.journal.domain
    pingback_url = urlencode({'pingback': 'http://{0}{1}'.format(domain, reverse('crossref_pingback'))})

    test_url = '{0}&{1}'.format(CROSSREF_TEST_URL, pingback_url)
    live_url = '{0}?{1}'.format(CROSSREF_LIVE_URL, pingback_url)

    use_crossref = setting_handler.get_setting('Identifiers', 'use_crossref',
                                               identifier.article.journal).processed_value

    if not use_crossref:
        logger.info("[DOI] Not using Crossref DOIs on this journal. Aborting registration.")
        return 'Crossref Disabled', 'Disabled'

    test_mode = setting_handler.get_setting('Identifiers', 'crossref_test', identifier.article.journal).processed_value

    if test_mode:
        util_models.LogEntry.add_entry('Submission', "DOI registration running in test mode", 'Info',
                                       target=identifier.article)
    else:
        util_models.LogEntry.add_entry('Submission', "DOI registration running in live mode", 'Info',
                                       target=identifier.article)

    return send_crossref_deposit(test_url if test_mode else live_url, identifier)


def register_crossref_component(article, xml, supp_file):
    from utils import setting_handler

    test_url = CROSSREF_TEST_URL
    live_url = CROSSREF_LIVE_URL

    use_crossref = setting_handler.get_setting('Identifiers', 'use_crossref',
                                               article.journal).processed_value

    if not use_crossref:
        logger.info("[DOI] Not using Crossref DOIs on this journal. Aborting registration.")
        return

    test_mode = setting_handler.get_setting('Identifiers', 'crossref_test', article.journal).processed_value

    server = test_url if test_mode else live_url

    if test_mode:
        util_models.LogEntry.add_entry('Submission', "DOI component registration running in test mode", 'Info',
                                       target=article)
    else:
        util_models.LogEntry.add_entry('Submission', "DOI component registration running in live mode", 'Info',
                                       target=article)

    response = requests.post(server, data=xml.encode('utf-8'),
                             auth=(setting_handler.get_setting('Identifiers',
                                                               'crossref_username',
                                                               article.journal).processed_value,
                                   setting_handler.get_setting('Identifiers', 'crossref_password',
                                                               article.journal).processed_value),
                             headers={"Content-Type": "application/vnd.crossref.deposit+xml"})

    if response.status_code != 200:
        util_models.LogEntry.add_entry('Error',
                                       "Error depositing: {0}. {1}".format(response.status_code, response.text),
                                       'Debug',
                                       target=article)
        logger.error("Error depositing: {}".format(response.status_code))
        logger.error(response.text, file=sys.stderr)
    else:
        token = response.json()['message']['batch-id']
        status = response.json()['message']['status']
        util_models.LogEntry.add_entry('Submission', "Deposited {0}. Status: {1}".format(token, status), 'Info',
                                       target=article)
        logger.info("Status of {} in {}: {}".format(token, '{0}.{1}'.format(article.get_doi(), supp_file.pk), status))


def send_crossref_deposit(server, identifier):
    # todo: work out whether this is acceptance or publication
    # if it's acceptance, then we use "0" for volume and issue
    # if publication, then use real values
    # the code here is for acceptance

    from utils import setting_handler
    article = identifier.article
    error = False

    template_context = {
        'batch_id': uuid4(),
        'timestamp': int(round((datetime.datetime.now() - datetime.datetime(1970, 1, 1)).total_seconds())),
        'depositor_name': setting_handler.get_setting('Identifiers', 'crossref_name',
                                                      identifier.article.journal).processed_value,
        'depositor_email': setting_handler.get_setting('Identifiers', 'crossref_email',
                                                       identifier.article.journal).processed_value,
        'registrant': setting_handler.get_setting('Identifiers', 'crossref_registrant',
                                                  identifier.article.journal).processed_value,
        'journal_title': identifier.article.journal.name,
        'journal_issn': identifier.article.journal.issn,
        'date_published': identifier.article.date_published,
        'issue': identifier.article.issue,
        'article_title': '{0}{1}{2}'.format(
            identifier.article.title,
            ' ' if identifier.article.subtitle is not None else '',
            identifier.article.subtitle if identifier.article.subtitle is not None else ''),
        'authors': identifier.article.authors.all(),
        'doi': identifier.identifier,
        'article_url': identifier.article.url,
        'now': timezone.now(),
    }

    pdfs = identifier.article.pdfs
    if len(pdfs) > 0:
        template_context['pdf_url'] = article.pdf_url

    if article.license:
        template_context["license"] = article.license.url

    template = 'identifiers/crossref.xml'
    crossref_template = render_to_string(template, template_context)
    logger.debug(crossref_template)

    util_models.LogEntry.add_entry('Submission', "Sending request to {1}: {0}".format(crossref_template, server),
                                   'Info',
                                   target=identifier.article)

    response = requests.post(server, data=crossref_template.encode('utf-8'),
                             auth=(setting_handler.get_setting('Identifiers',
                                                               'crossref_username',
                                                               identifier.article.journal).processed_value,
                                   setting_handler.get_setting('Identifiers', 'crossref_password',
                                                               identifier.article.journal).processed_value),
                             headers={"Content-Type": "application/vnd.crossref.deposit+xml"})

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
        logger.error(response.text)
        error = True
    else:
        token = response.json()['message']['batch-id']
        status = response.json()['message']['status']
        util_models.LogEntry.add_entry('Submission', "Deposited {0}. Status: {1}".format(token, status), 'Info',
                                       target=identifier.article)
        status = "Status of {} in {}: {}".format(token, identifier.identifier, status)
        logger.info(status)

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
        template = 'identifiers/crossref.xml'
        crossref_template = render_to_string(template, template_context)

        pdfs = identifier.article.pdfs
        if len(pdfs) > 0:
            template_context['pdf_url'] = identifier.article.pdf_url

        response = requests.post(url, data=crossref_template.encode('utf-8'),
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
