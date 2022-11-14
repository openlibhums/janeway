__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


import datetime
from uuid import uuid4
import requests
from bs4 import BeautifulSoup
import time
import itertools

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
from utils.shared import clear_cache
from utils import setting_handler, render_template
from crossref.restful import Depositor
from identifiers import models
from submission import models as submission_models

logger = get_logger(__name__)

CROSSREF_TIMEOUT_SECONDS = 30

def register_crossref_doi(identifier):
    return register_batch_of_crossref_dois([identifier.article])


def register_batch_of_crossref_dois(articles, **kwargs):
    journals = set([article.journal for article in articles])
    if len(journals) > 1:
        status = 'Articles must all be from the same journal'
        error = True
        logger.debug(status)
        return status, error
    else:
        journal = journals.pop()

    use_crossref, test_mode, missing_settings = check_crossref_settings(journal)

    if use_crossref and not missing_settings:
        mode = 'test' if test_mode else 'live'
        desc = f'DOI registration running in f{mode} mode'
        util_models.LogEntry.bulk_add_simple_entry('Submission', desc, 'Info', targets=articles)
        identifiers = get_dois_for_articles(articles, create=True)
        return send_crossref_deposit(test_mode, identifiers, journal)
    elif not use_crossref:
        status = f'Crossref Disabled ({journal.code})'
        error = True
        logger.debug(status)
        return status, error
    elif use_crossref and missing_settings:
        status = f'Missing Crossref settings ({journal.code}): '+', '.join(missing_settings)
        error = True
        logger.debug(status)
        return status, error


@cache(30)
def check_crossref_settings(journal):
    use_crossref = setting_handler.get_setting(
        'Identifiers',
        'use_crossref',
        journal
    ).processed_value

    if not use_crossref:
        logger.info("[DOI] Not using Crossref DOIs on this journal. " \
                    "Aborting registration.")

    test_mode = setting_handler.get_setting(
        'Identifiers',
        'crossref_test',
        journal
    ).processed_value or settings.DEBUG

    settings_to_check = [
        'crossref_prefix',
        'crossref_username',
        'crossref_password',
        'crossref_name',
        'crossref_email',
        'crossref_registrant'
    ]
    missing_settings = []
    for setting_name in settings_to_check:
        setting_value = setting_handler.get_setting(
            'Identifiers',
            setting_name,
            journal
        ).processed_value
        if not setting_value:
            missing_settings.append(setting_name)
    if not journal.code:
        missing_settings.append('journal__code')

    return use_crossref, test_mode, missing_settings


@cache(30)
def get_poll_settings(journal):
    test_mode = setting_handler.get_setting('Identifiers',
                                            'crossref_test',
                                            journal).processed_value or settings.DEBUG
    username = setting_handler.get_setting('Identifiers', 'crossref_username',
                                           journal).processed_value
    password = setting_handler.get_setting('Identifiers', 'crossref_password',
                                               journal).processed_value
    return test_mode, username, password


def get_dois_for_articles(articles, create=False):
    identifiers = []
    for article in articles:
        try:
            identifier = article.get_identifier('doi', object=True)
            if not identifier and create:
                identifier = generate_crossref_doi_with_pattern(article)
            if identifier:
                identifiers.append(identifier)
        except AttributeError as e:
            logger.debug(f'Error with article {article.pk}: {e}')
    return identifiers


def poll_dois_for_articles(articles, **kwargs):
    clear_cache()

    start = kwargs.pop('start', time.time())
    timeout = kwargs.pop('timeout', CROSSREF_TIMEOUT_SECONDS)

    status = ''
    error = False
    identifiers = get_dois_for_articles(articles)
    polled = set()
    for i, identifier in enumerate(identifiers):

        # Time out gracefully
        if timeout and time.time() > start + timeout:
            error = True
            journal_code = identifier.article.journal.code
            status = f"Polling timed out before all articles could be checked. Polled: {i} of {len(identifiers)} ({journal_code})."
            break

        try:
            deposit = identifier.crossrefstatus.latest_deposit
        except AttributeError:
            deposit = None
        if deposit and deposit not in polled:
            try:
                status, error = deposit.poll()
                polled.add(deposit)
                if len(polled) and len(polled) % 20 == 0:
                    time.sleep(.15)
            except:
                continue

        try:
            identifier.crossrefstatus.update()
        except AttributeError:
            crossref_status = models.CrossrefStatus.objects.create(
                identifier=identifier
            )
            crossref_status.update()

    return status, error

def register_crossref_component(article, xml, supp_file):
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


def create_crossref_doi_batch_context(journal, identifiers):
    timestamp_suffix = journal.get_setting(
        'crossref',
        'crossref_date_suffix',
    )

    template_context = {
        'batch_id': uuid4(),
        'now': timezone.now(),
        'timestamp': int(round((datetime.datetime.now() - datetime.datetime(1970, 1, 1)).total_seconds())),
        'timestamp_suffix': timestamp_suffix,
        'depositor_name': setting_handler.get_setting('Identifiers', 'crossref_name',
                                                      journal).processed_value,
        'depositor_email': setting_handler.get_setting('Identifiers', 'crossref_email',
                                                       journal).processed_value,
        'registrant': setting_handler.get_setting('Identifiers', 'crossref_registrant',
                                                  journal).processed_value,
        'is_conference': journal.is_conference or False,
    }

    template_context['crossref_issues'] = create_crossref_issues_context(journal, identifiers)
    return template_context


def create_crossref_issues_context(journal, identifiers):
    crossref_issues = []

    # First pull out and handle individually any articles with
    # ISSN overrides or custom publication_titles
    identifiers_covered = set()
    for identifier in identifiers:
        article = identifier.article
        if article.ISSN_override or article.publication_title:
            special_identifier_set = set([identifier])
            identifiers_covered.add(identifier)
            issue = article.issue
            crossref_issue = create_crossref_issue_context(
                journal,
                special_identifier_set,
                issue,
                ISSN_override=article.ISSN_override,
                publication_title=article.publication_title,
            )
            crossref_issues.append(crossref_issue)
    remaining_identifiers = identifiers - identifiers_covered

    # Then handle the rest
    for issue in set(
        (identifier.article.issue for identifier in remaining_identifiers)
    ):
        crossref_issue = create_crossref_issue_context(
            journal,
            remaining_identifiers,
            issue,
        )
        crossref_issues.append(crossref_issue)

    return crossref_issues


def create_crossref_issue_context(
    journal,
    identifiers,
    issue,
    ISSN_override=None,
    publication_title=None,
):
    crossref_issue = {}
    crossref_issue['journal'] = create_crossref_journal_context(
        journal,
        ISSN_override,
        publication_title,
    )
    crossref_issue['issue'] = issue

    crossref_issue['articles'] = []
    for identifier in identifiers:
        article = identifier.article
        if article.issue == issue:
            article_context = create_crossref_article_context(article, identifier)
            crossref_issue['articles'].append(article_context)

    return crossref_issue


@cache(30)
def create_crossref_journal_context(
    journal,
    ISSN_override=None,
    publication_title=None
):
    journal_data = {
        'title': publication_title or journal.name,
        'journal_issn': ISSN_override or journal.issn,
        'print_issn': journal.print_issn,
        'press': journal.press,
    }
    if journal.doi:
        journal_data["doi"] = journal.doi
        journal_data["url"] = journal.site_url()

    return journal_data

def create_crossref_article_context(article, identifier=None):
    template_context = {
        'id': article.pk,
        'title': '{0}{1}{2}'.format(
            article.title,
            ' ' if article.subtitle is not None else '',
            article.subtitle if article.subtitle is not None else ''),
        'doi': identifier.identifier if identifier else render_doi_from_pattern(article),
        'url': article.url,
        'authors': article.frozenauthor_set.all(),
        'abstract': strip_tags(article.abstract or ''),
        'date_accepted': article.date_accepted,
        'date_published': article.date_published,
        'license': article.license.url if article.license else '',
        'pages': article.page_numbers,
        'scheduled': article.scheduled_for_publication,
    }

    # append citations for i4oc compatibility
    template_context["citation_list"] = extract_citations_for_crossref(article)

    # append PDFs for similarity check compatibility
    pdfs = article.pdfs
    if len(pdfs) > 0:
        template_context['pdf_url'] = article.pdf_url

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


def send_crossref_deposit(test_mode, identifiers, journal=None):
    """
    Generates the crossref deposit model instances,
    crossref status model instances, and XML documents,
    attempts to send the deposits, and creates logs.
    :param test_mode: boolean
    :param identifiers: iterable of Identifier model instances
    :return: tuple consisting of (str, bool)
    """

    # Form a set from the iterable passed in
    identifiers = set((i for i in identifiers))

    # Get the journal
    # It assumes all the identifiers are for the same journal
    if not journal:
        first, *_ = identifiers
        journal = first.article.journal

    error = False

    template = 'common/identifiers/crossref_doi_batch.xml'
    template_context = create_crossref_doi_batch_context(
        journal,
        identifiers,
    )
    document = render_to_string(template, template_context)

    filename = uuid4()

    crossref_deposit = models.CrossrefDeposit.objects.create(document=document, file_name=filename)
    crossref_deposit.save()
    for identifier in identifiers:
        crossref_status, _created = models.CrossrefStatus.objects.get_or_create(identifier=identifier)
        crossref_status.deposits.add(crossref_deposit)
        crossref_status.save()

    description = "Sending request: {0}".format(crossref_deposit.document)
    articles = set([identifier.article for identifier in identifiers])
    util_models.LogEntry.bulk_add_simple_entry('Submission', description, 'Info', targets=articles)

    doi_prefix = setting_handler.get_setting('Identifiers', 'crossref_prefix', journal).processed_value
    username = setting_handler.get_setting('Identifiers', 'crossref_username', journal).processed_value
    password = setting_handler.get_setting('Identifiers', 'crossref_password', journal).processed_value

    depositor = Depositor(prefix=doi_prefix, api_user=username, api_key=password, use_test_server=test_mode)

    try:
        response = depositor.register_doi(submission_id=filename, request_xml=crossref_deposit.document)
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
        status = 'Error depositing. Could not connect to Crossref ({0}). Error: {1}'.format(
            depositor.get_endpoint(verb='deposit'),
            e,
        )
        crossref_deposit.result_text = status
        crossref_deposit.save()
        util_models.LogEntry.bulk_add_simple_entry('Error', status, 'Debug', targets=articles)
        logger.error(status)
        return status, error

    pks = ",".join([str(article.pk) for article in articles])
    logger.debug(f"[CROSSREF:DEPOSIT:{pks}] Sending")
    logger.debug(f"[CROSSREF:DEPOSIT:{pks}] Response code {response.status_code}")

    if response.status_code != 200:
        status = "Error depositing: {0}. {1}".format(response.status_code, response.text)
        crossref_deposit.result_text = status
        crossref_deposit.save()
        util_models.LogEntry.bulk_add_simple_entry('Error', status, 'Debug', targets=articles)
        logger.error(status)
        error = True
    else:
        status = f"Deposit sent ({journal.code})"
        util_models.LogEntry.bulk_add_simple_entry('Submission', status, 'Info', targets=articles)
        logger.info(status)

    for identifier in identifiers:
        crossref_status = models.CrossrefStatus.objects.get(identifier=identifier)
        crossref_status.update()

    return status, error


def create_crossref_doi_identifier(article, doi_suffix=None, suffix_is_whole_doi=False):
    """ Creates (but does not register remotely) a Crossref DOI

    :param article: the article for which to create the DOI
    :param doi_suffix: an optional DOI suffix
    :return:
    """

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

    return models.Identifier.objects.create(**doi_options)


def generate_crossref_doi_with_pattern(article):
    """
    Creates a crossref doi utilising a preset pattern.
    :param article: article objects
    :return: returns a DOI
    """

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

    return models.Identifier.objects.create(**doi_options)


@cache(600)
def render_doi_from_pattern(article):
    doi_prefix = setting_handler.get_setting('Identifiers', 'crossref_prefix', article.journal).value
    doi_suffix = render_template.get_requestless_content({'article': article},
                                                         article.journal,
                                                         'doi_pattern',
                                                         group_name='Identifiers')
    return '{0}/{1}'.format(doi_prefix, doi_suffix)


def preview_registration_information(article):
    """
    Generates a rudimentary printout of metadata
    for proofing by the end user before attempting
    to register the DOI with Crossref.
    """
    if article.journal.use_crossref:
        doi = article.get_identifier('doi', object=True)
        crossref_context = create_crossref_article_context(article, doi)

        exclude = ['citation_list']
        for k in exclude:
            crossref_context.pop(k)

        metadata_printout = 'Current metadata to send to Crossref:<br>'

        for k, v in crossref_context.items():
            if k == 'authors':
                for idx, author in enumerate(crossref_context['authors'], start=1):
                    for prop in ['first_name', 'middle_name', 'last_name',
                                 'department', 'institution', 'orcid']:
                        val = getattr(author, prop) or ''
                        metadata_printout += f'<br>author{str(idx)}_{prop}: {val}'
            else:
                metadata_printout += f'<br>{k}: {"" if v == None else v}'
        return metadata_printout

    else:
        return ''

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


def generate_issue_doi_from_logic(issue):
    doi_prefix = setting_handler.get_setting(
        'Identifiers', 'crossref_prefix', issue.journal).value
    doi_suffix = render_template.get_requestless_content(
        {'issue': issue},
        issue.journal,
        'issue_doi_pattern',
        group_name='Identifiers')
    return '{0}/{1}'.format(doi_prefix, doi_suffix)


def auto_assign_issue_doi(issue):
    auto_assign_enabled = setting_handler.get_setting(
        'Identifiers', 'use_crossref', issue.journal,
        default=True,
    ).processed_value
    if auto_assign_enabled and not issue.doi:
        issue.doi = generate_issue_doi_from_logic(issue)
        issue.save()


def on_article_assign_to_issue(article, issue, user):
    auto_assign_issue_doi(issue)
