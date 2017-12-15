import re

import requests
from bs4 import BeautifulSoup

from utils.importers import shared
from submission import models
from journal import models as journal_models
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from utils import models as utils_models
from core import models as core_models


# note: URL to pass for import is http://journal.org/jms/index.php/up/oai/


def get_thumbnails(url):
    """ Extract thumbnails from a Ubiquity Press site. This is run once per import to get the base thumbnail URL.

    :param url: the base URL of the journal
    :return: the thumbnail for this article
    """
    print("Extracting thumbnails.")

    url_to_use = url + '/articles/?f=1&f=3&f=2&f=4&f=5&order=date_published&app=100000'
    resp, mime = utils_models.ImportCacheEntry.fetch(url=url_to_use)

    soup = BeautifulSoup(resp)

    article = soup.find('div', attrs={'class': 'article-image'})
    article = BeautifulSoup(str(article))

    id_href = shared.get_soup(article.find('img'), 'src')

    if id_href.endswith('/'):
        id_href = id_href[:-1]
    id_href_split = id_href.split('/')
    id_href = id_href_split[:-1]
    id_href = '/'.join(id_href)[1:]

    return id_href


def import_article(journal, user, url, thumb_path=None):
    """ Import a Ubiquity Press article.

    :param journal: the journal to import to
    :param user: the user who will own the file
    :param url: the URL of the article to import
    :param thumb_path: the base path for thumbnails
    :return: None
    """

    # retrieve the remote page and establish if it has a DOI
    already_exists, doi, domain, soup_object = shared.fetch_page_and_check_if_exists(url)
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    if already_exists:
        # if here then this article has already been imported
        return

    # fetch basic metadata
    new_article = shared.get_and_set_metadata(journal, soup_object, user, False, True)

    # try to do a license lookup
    pattern = re.compile(r'creativecommons')
    license_tag = soup_object.find(href=pattern)
    license_object = models.Licence.objects.filter(url=license_tag['href'].replace('http:', 'https:'), journal=journal)

    if len(license_object) > 0 and license_object[0] is not None:
        license_object = license_object[0]
        print("Found a license for this article: {0}".format(license_object.short_name))
    else:
        license_object = models.Licence.objects.get(name='All rights reserved', journal=journal)
        print("Did not find a license for this article. Using: {0}".format(license_object.short_name))

    new_article.license = license_object

    # determine if the article is peer reviewed
    peer_reviewed = soup_object.find(name='a', text='Peer Reviewed') is not None
    print("Peer reviewed: {0}".format(peer_reviewed))

    new_article.peer_reviewed = peer_reviewed

    # get PDF and XML galleys
    pdf = shared.get_pdf_url(soup_object)

    # rip XML out if found
    pattern = re.compile('.*?XML.*')
    xml = soup_object.find('a', text=pattern)
    html = None

    if xml:
        print("Ripping XML")
        xml = xml.get('href', None).strip()
    else:
        # looks like there isn't any XML
        # instead we'll pull out any div with an id of "xml-article" and add as an HTML galley
        print("Ripping HTML")
        html = soup_object.find('div', attrs={'id': 'xml-article'})

        if html:
            html = str(html.contents[0])

    # attach the galleys to the new article
    galleys = {
        'PDF': pdf,
        'XML': xml,
        'HTML': html
    }

    shared.set_article_galleys_and_identifiers(doi, domain, galleys, new_article, url, user)

    # fetch thumbnails
    if thumb_path is not None:
        print("Attempting to assign thumbnail.")

        final_path_element = url.split('/')[-1]
        id_regex = re.compile(r'.*?(\d+)')
        matches = id_regex.match(final_path_element)
        article_id = matches.group(1)

        print("Determined remote article ID as: {0}".format(article_id))
        print("Thumbnail path: {thumb_path}, URL: {url}".format(thumb_path=thumb_path, url=url))

        try:
            filename, mime = shared.fetch_file(domain, thumb_path + "/" + article_id, "", 'graphic',
                                               new_article, user)
            shared.add_file(mime, 'graphic', 'Thumbnail', user, filename, new_article, thumbnail=True)
        except BaseException:
            print("Unable to import thumbnail. Recoverable error.")

    # try to do a license lookup

    # save the article to the database
    new_article.save()


def import_oai(journal, user, soup, domain):
    """ Initiate an OAI import on a Ubiquity Press journal.

        :param journal: the journal to import to
        :param user: the user who will own imported articles
        :param soup: the BeautifulSoup object of the OAI feed
        :param domain: the domain of the journal (for extracting thumbnails)
        :return: None
        """

    thumb_path = get_thumbnails(domain)

    identifiers = soup.findAll('dc:identifier')

    for identifier in identifiers:
        # rewrite the phrase /jms in Ubiquity Press OAI feeds to get version with
        # full and proper email metadata
        identifier.contents[0] = identifier.contents[0].replace('/jms', '')
        if identifier.contents[0].startswith('http'):
            print('Parsing {0}'.format(identifier.contents[0]))

            import_article(journal, user, identifier.contents[0], thumb_path)

    import_issue_images(journal, user, domain[:-1])
    import_journal_metadata(journal, user, domain[:-1])


def import_journal_metadata(journal, user, url):
    base_url = url

    issn = re.compile(r'E-ISSN: (\d{4}-\d{4})')
    publisher = re.compile(r'Published by (.*)')

    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    print("Extracting journal-level metadata...")

    resp, mime = utils_models.ImportCacheEntry.fetch(url=base_url)

    soup = BeautifulSoup(resp, 'lxml')

    issn_result = soup.find(text=issn)
    issn_match = issn.match(str(issn_result).strip())

    print('ISSN set to: {0}'.format(issn_match.group(1)))
    journal.issn = issn_match.group(1)

    try:
        publisher_result = soup.find(text=publisher)
        publisher_match = str(publisher_result.next_sibling.getText()).strip()
        print('Publisher set to: {0}'.format(publisher_match))
        journal.publisher = publisher_match
        journal.save()
    except BaseException:
        print("Error setting publisher.")


def parse_backend_list(url, auth_file, auth_url, regex):
    html_body, mime = utils_models.ImportCacheEntry.fetch(url, up_base_url=auth_url, up_auth_file=auth_file)

    matches = re.findall(regex, html_body.decode())

    # look for next_page
    soup_object = BeautifulSoup(html_body, 'lxml')
    soup = soup_object.find(text='>')

    if soup:
        href = soup.parent.attrs['href']
        matches += parse_backend_list(href, auth_file, auth_url, regex)

    return matches


def get_article_list(url, list_type, auth_file):

    auth_url = url

    regex = '\/jms\/editor\/submissionReview\/(\d+)'

    if list_type == 'in_review':
        url += '/jms/editor/submissions/submissionsInReview'
        regex = '\/jms\/editor\/submissionReview\/(\d+)'
    elif list_type == 'unassigned':
        url += '/jms/editor/submissions/submissionsUnassigned'
        regex = '\/jms\/editor\/submission\/(\d+)'
    elif list_type == 'in_editing':
        url += '/jms/editor/submissions/submissionsInEditing'
        regex = '\/jms\/editor\/submissionEditing\/(\d+)'
    elif list_type == 'archive':
        url += '/jms/editor/submissions/submissionsArchives'
        regex = '\/jms\/editor\/submissionEditing\/(\d+)'
    else:
        return None

    matches = parse_backend_list(url, auth_file, auth_url, regex)

    return matches


def parse_backend_user_list(url, auth_file, auth_url, regex):
    html_body, mime = utils_models.ImportCacheEntry.fetch(url, up_base_url=auth_url, up_auth_file=auth_file)

    matches = re.findall(regex, html_body.decode())

    # look for next_page
    soup_object = BeautifulSoup(html_body, 'lxml')
    soup = soup_object.find(text='>')

    if soup:
        href = soup.parent.attrs['href']
        matches += parse_backend_user_list(href, auth_file, auth_url, regex)

    return matches


def get_user_list(url, auth_file):

    auth_url = url

    url += '/jms/manager/people/all'
    regex = '\/jms\/manager\/userProfile\/(\d+)'

    matches = parse_backend_user_list(url, auth_file, auth_url, regex)

    return matches


def import_issue_images(journal, user, url):
    base_url = url

    if not url.endswith('/issue/archive/'):
        url += '/issue/archive/'

    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    resp, mime = utils_models.ImportCacheEntry.fetch(url=url)

    soup = BeautifulSoup(resp, 'lxml')

    import core.settings
    import os
    from django.core.files import File

    for issue in journal.issues():
        pattern = re.compile(r'\/\d+\/volume\/{0}\/issue\/{1}'.format(issue.volume, issue.issue))
        img_url = base_url + soup.find(src=pattern)['src']
        print("Fetching {0}".format(img_url))

        resp, mime = utils_models.ImportCacheEntry.fetch(url=img_url)

        path = os.path.join(core.settings.BASE_DIR, 'files', 'journals', str(journal.id))

        os.makedirs(path, exist_ok=True)

        path = os.path.join(path, 'volume{0}_issue_{0}.graphic'.format(issue.volume, issue.issue))

        with open(path, 'wb') as f:
            f.write(resp)

        with open(path, 'rb') as f:
            issue.cover_image.save(path, File(f))

        sequence_pattern = re.compile(r'.*?(\d+)\/volume\/{0}\/issue\/{1}.*'.format(issue.volume, issue.issue))

        issue.order = int(sequence_pattern.match(img_url).group(1))

        print("Setting Volume {0}, Issue {1} sequence to: {2}".format(issue.volume, issue.issue, issue.order))

        print("Extracting section orders within the issue...")

        new_url = '/{0}/volume/{1}/issue/{2}/'.format(issue.order, issue.volume, issue.issue)
        resp, mime = utils_models.ImportCacheEntry.fetch(url=base_url + new_url)

        soup_issue = BeautifulSoup(resp, 'lxml')

        sections_to_order = soup_issue.find_all(name='h2', attrs={'class': 'main-color-text'})

        section_order = 0

        # delete existing order models for sections for this issue
        journal_models.SectionOrdering.objects.filter(issue=issue).delete()

        for section in sections_to_order:
            print('[{0}] {1}'.format(section_order, section.getText()))
            order_section, c = models.Section.objects.language('en').get_or_create(
                name=section.getText().strip(),
                journal=journal)
            journal_models.SectionOrdering.objects.create(issue=issue,
                                                          section=order_section,
                                                          order=section_order).save()
            section_order += 1

        print("Extracting article orders within the issue...")

        # delete existing order models for issue
        journal_models.ArticleOrdering.objects.filter(issue=issue).delete()

        pattern = re.compile(r'\/articles\/(.+?)/(.+?)/')
        articles = soup_issue.find_all(href=pattern)

        article_order = 0

        processed = []

        for article_link in articles:
            # parse the URL into a DOI and prefix
            match = pattern.match(article_link['href'])
            prefix = match.group(1)
            doi = match.group(2)

            # get a proper article object
            article = models.Article.get_article(journal, 'doi', '{0}/{1}'.format(prefix, doi))

            if article and article not in processed:

                journal_models.ArticleOrdering.objects.create(issue=issue,
                                                              article=article,
                                                              order=article_order)

                article_order += 1

            processed.append(article)

        issue.save()


def import_jms_user(url, journal, auth_file, base_url, user_id):
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    # Fetch the user profile page and parse its metdata
    resp, mime = utils_models.ImportCacheEntry.fetch(url=url, up_auth_file=auth_file, up_base_url=base_url)
    soup_user_profile = BeautifulSoup(resp, 'lxml')
    profile_dict = shared.get_user_profile(soup_user_profile)[0]

    # add an account for this new user
    account = core_models.Account.objects.filter(email=profile_dict['email'])

    if account is not None and len(account) > 0:
        account = account[0]
        print("Found account for {0}".format(profile_dict['email']))
    else:
        print("Didn't find account for {0}. Creating.".format(profile_dict['email']))

        if profile_dict['Country'] == '—':
            profile_dict['Country'] = None
        else:
            try:
                profile_dict['Country'] = core_models.Country.objects.get(name=profile_dict['Country'])
            except:
                print("Country not found")
                profile_dict['Country'] = None

        account = core_models.Account.objects.create(email=profile_dict['email'],
                                                     username=profile_dict['Username'],
                                                     institution=profile_dict['Affiliation'],
                                                     first_name=profile_dict['First Name'],
                                                     last_name=profile_dict['Last Name'],
                                                     middle_name=profile_dict.get('Middle Name', None),
                                                     country=profile_dict.get('Country', None),
                                                     biography=profile_dict.get('Bio Statement', None),
                                                     salutation=profile_dict.get('Salutation', None))
        account.save()

        if account:
            account.add_account_role(journal=journal, role_slug='author')
            account.add_account_role(journal=journal, role_slug='reviewer')



def import_in_review_article(url, journal, auth_file, base_url, article_id):
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    # Fetch the summary page and parse its metdata
    resp, mime = utils_models.ImportCacheEntry.fetch(url=url, up_auth_file=auth_file, up_base_url=base_url)
    soup_article_summary = BeautifulSoup(resp, 'lxml')
    summary_dict = shared.get_metadata(soup_article_summary)

    # Fetch the review page and parse its data
    review_url = '{base_url}/jms/editor/submissionReview/{article_id}'.format(base_url=base_url, article_id=article_id)
    resp, mime = utils_models.ImportCacheEntry.fetch(url=review_url, up_auth_file=auth_file, up_base_url=base_url)
    soup_article_review = BeautifulSoup(resp, 'lxml')
    files = shared.get_files(soup_article_review)
    print(files)

    # Fetch peer-reviewers
    peer_reviewers = shared.get_peer_reviewers(soup_article_review)
    print(peer_reviewers)

    # Get article status
    article_status = shared.get_jms_article_status(soup_article_review)
    print(article_status)