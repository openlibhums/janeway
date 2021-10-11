__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
from submission import models
from journal import models as journal_models
from core import models as core_models

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from utils.importers import up, ojs


def clear_db(journal):
    """ Deletes all articles, issues and all non-admin users from the specified journal.

    :param journal: the journal to act upon
    :return: None
    """
    print('Deleting all articles, issues and all non-admin users')
    all_articles = models.Article.objects.filter(journal=journal)

    all_articles.delete()

    issues = journal_models.Issue.objects.filter(journal=journal)

    issues.delete()

    all_users = core_models.Account.objects.filter(is_admin=False)

    for acc in all_users:
        acc.delete()


def identify_journal_type_by_oai(url):
    """ Attempts to identify the type of journal we are dealing with based on the OAI URL.

    :param url: the URL to the OAI feed
    :return: a string containing the type of journal
    """
    if u'/jms/' in url:
        return "UP"

    if (u'?journal=' in url and u'?page=oai') or '/oai' in url:
        return "OJS"


def import_ojs_article(**options):
    """ Imports a single article from an Open Journal Systems installation

    :param options: a dictionary containing 'journal_id', 'user_id', 'url' and optionally a 'delete' flag
    :return: None
    """
    journal = journal_models.Journal.objects.get(pk=options['journal_id'])
    user = core_models.Account.objects.get(pk=options['user_id'])
    url = options['url']

    if options['delete']:
        clear_db(journal)

    ojs.import_article(journal, user, url)


def import_up_article(**options):
    """ Imports a single article from a Ubiquity Press installation

    :param options: a dictionary containing 'journal_id', 'user_id', 'url' and optionally a 'delete' flag
    :return: None
    """
    journal = journal_models.Journal.objects.get(pk=options['journal_id'])
    user = core_models.Account.objects.get(pk=options['user_id'])
    url = options['url']

    if options['delete']:
        clear_db(journal)
    update = options.get("update", False)

    up.import_article(journal, user, url, update=update)


def import_all(**options):
    """ Imports all the content from a UP journal

    We overload the import_issue_images function setting load_missing,
    which will import all articles that have not yet been imported.
    This turns the function into an 'import all content'

    :param options: a dictionary containing 'journal_id', 'user_id', and a 'url'
    :return: None
    """
    journal = journal_models.Journal.objects.get(code=options['journal_code'])
    user = core_models.Account.objects.get(pk=options['user_id'])
    url = options['url']
    update = options.get("update", False)

    up.import_issue_images(
        journal, user, url, import_missing=True, update=update)


def import_issue_images(**options):
    """ Imports a issue images and sequencing of sections/articles from a UP journal

    :param options: a dictionary containing 'journal_id', 'user_id', and a 'url'
    :return: None
    """
    journal = journal_models.Journal.objects.get(pk=options['journal_id'])
    user = core_models.Account.objects.get(pk=options['user_id'])
    url = options['url']

    up.import_issue_images(journal, user, url, update=options.get("update"))


def import_journal_metadata(**options):
    """ Imports journal-level metadata from a UP journal

    :param options: a dictionary containing 'journal_id', 'user_id', and a 'url'
    :return: None
    """
    journal = journal_models.Journal.objects.get(pk=options['journal_id'])
    user = core_models.Account.objects.get(pk=options['user_id'])
    url = options['url']

    up.import_journal_metadata(journal, user, url)


def import_oai(**options):
    """ Imports an OAI feed

    :param options: a dictionary containing 'journal_id', 'user_id', 'url' and optionally a 'delete' flag
    :return: None
    """
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    journal = journal_models.Journal.objects.get(pk=options['journal_id'])
    user = core_models.Account.objects.get(pk=options['user_id'])

    if options['delete']:
        clear_db(journal)

    parse_OAI(journal, options, user)


def parse_OAI(journal, options, user, resume=None):

    if resume:
        verb = '?verb=ListRecords&resumptionToken={0}'.format(resume)
    else:
        verb = '?verb=ListRecords&metadataPrefix=oai_dc'

    url = options['url'] + verb
    update = options.get("update", False)

    journal_type = identify_journal_type_by_oai(url)
    parsed_uri = urlparse(url)
    domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)

    # note: we're not caching OAI pages as they update regularly
    page = requests.get(url, verify=False)
    soup = BeautifulSoup(page.text, "lxml")

    if journal_type == "UP":
        print("Detected journal type as UP. Processing.")
        up.import_oai(journal, user, soup, domain, update=update)
    elif journal_type == "OJS":
        print("Detected journal type as OJS. Processing.")
        ojs.import_oai(journal, user, soup)
    else:
        print("Journal type currently unsupported")

    # see if there is a resumption token
    resume = soup.find('resumptiontoken')

    if resume:
        resume = resume.getText()

    if resume and resume != '':
        print('Executing resumeToken')
        parse_OAI(journal, options, user, resume=resume)

    return soup
