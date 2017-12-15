import os
import urllib
from datetime import datetime
from urllib.parse import urlparse
from uuid import uuid4
import re
from dateutil import parser as dateparser
import requests
from bs4 import BeautifulSoup

from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from core import models as core_models
from journal import models as journal_models
from submission import models as submission_models
from identifiers import models as identifiers_models
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from utils import models as utils_models
from utils import shared as utils_shared


def fetch_images_and_rewrite_xml_paths(base, root, contents, article, user):
    """Download images from an XML or HTML document and rewrite the new galley to point to the correct source.

    :param base: a base URL for the remote journal install e.g. http://www.myjournal.org
    :param root: the root page (i.e. the article that we are grabbing from) e.g. /article/view/27
    :param contents: the current page's HTML or XML
    :param article: the new article to which this download should be attributed
    :param user: the user who will be assigned as the file owner of any downloaded file
    :return: a string of the rewritten XML or HTML
    """

    # create a BeautifulSoup instance of the page's HTML or XML
    soup = BeautifulSoup(contents, 'lxml')

    # add element:attribute properties here for images that should be downloaded and have their paths rewritten
    # so 'img':'src' means look for elements called 'img' with an attribute 'src'
    elements = {
        'img': 'src',
        'graphic': 'xlink:href'
    }

    # iterate over all found elements
    for element, attribute in elements. items():
        images = soup.findAll(element)

        # iterate over all found elements of each type in the elements dictionary
        for idx, val in enumerate(images):

            # attempt to pull a URL from the specified attribute
            url = get_soup(val, attribute)

            if url:
                url_to_use = url

                # this is a Ubiquity Press-specific fix to rewrite the path so that we don't hit OJS's dud backend
                if not url.startswith('/') and not url.startswith('http'):
                    url_to_use = root.replace('/article/view', '/articles') + '/' + url

                # download the image file
                filename, mime = fetch_file(base, url_to_use, root, '', article, user, handle_images=False)

                # determine the MIME type and slice the first open bracket and everything after the comma off
                mime = mime.split(',')[0][1:].replace("'", "")

                # store this image in the database affiliated with the new article
                new_file = add_file(mime, '', 'Galley image', user, filename, article, False)
                absolute_new_filename = reverse('article_file_download',
                                                kwargs={'identifier_type': 'id', 'identifier': article.id,
                                                        'file_id': new_file.id})

                # rewrite the HTML or XML contents to point to the new image filename (a reverse lookup of
                # article_file_download)
                print('Replacing image URL {0} with {1}'.format(url, absolute_new_filename))
                contents = str(contents).replace(url, absolute_new_filename)

    return contents


def parse_date(date_string, is_iso):
    """ Parse a date from a string according to timezone-specific settings

    :param date_string: the date string to be parsed
    :param is_iso: whether or not to use ISO-specific formatting settings ("%Y-%m-%dT%H:%M:%S" if True, otherwise
    "%Y-%m-%d"
    :return: a timezone object of the parsed date
    """
    if date_string is not None and date_string != "":
        if is_iso:
            return timezone.make_aware(datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S"),
                                       timezone.get_current_timezone())
        else:
            return timezone.make_aware(datetime.strptime(date_string, "%Y-%m-%d"), timezone.get_current_timezone())
    else:
        print("Returning current datetime as no valid datetime was given")
        return timezone.now()


def fetch_file(base, url, root, extension, article, user, handle_images=False):
    """ Download a remote file and store in the database affiliated to a specific article

    :param base: a base URL for the remote journal install e.g. http://www.myjournal.org
    :param url: either a full URL or a suffix to base that when concatenated will form a whole URL to the image
    :param root: either a full URL or a suffix to base that when concatenated will form a whole URL to the XML/HTML
    :param extension: the file extension of the file that we will download
    :param article: the new article to which this download should be attributed
    :param user: the user who will be assigned as the file owner of any downloaded file
    :param handle_images: whether or not to extract, download and parse images within the downloaded file
    :return: a tuple of the filename and MIME-type
    """

    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    # if this is not a full URL concatenate base and URL to form the full address
    if not url.startswith('http'):
        url = base + url

    print('Fetching {0}'.format(url))

    # imitate headers from a browser to avoid being blocked on some installs
    resp, mime = utils_models.ImportCacheEntry.fetch(url=url)

    # set the filename to a unique UUID4 identifier with the passed file extension
    filename = '{0}.{1}'.format(uuid4(), extension)

    # set the path to save to be the sub-directory for the article
    path = os.path.join(settings.BASE_DIR, 'files', 'articles', str(article.id))

    # create the sub-folders as necessary
    if not os.path.exists(path):
        os.makedirs(path, 0o0775)

    # intercept the request if we need to parse this as HTML or XML with images to rewrite
    if handle_images:
        resp = resp.decode()
        resp = fetch_images_and_rewrite_xml_paths(base, root, resp, article, user)

    if isinstance(resp, str):
        resp = bytes(resp, 'utf-8')

    with open(os.path.join(path, filename), 'wb') as f:
        print("Writing file {0} as binary".format(os.path.join(path, filename)))
        f.write(resp)

    # return the filename and MIME type
    return filename, mime


def save_file(base, contents, root, extension, article, user, handle_images=False):
    """ Save 'contents' to disk as a file associated with 'article'

    :param base: a base URL for the remote journal install e.g. http://www.myjournal.org
    :param contents: the contents to be written to disk
    :param root: either a full URL or a suffix to base that when concatenated will form a whole URL to the XML/HTML
    :param extension: the file extension of the file that we will download
    :param article: the new article to which this download should be attributed
    :param user: the user who will be assigned as the file owner of any downloaded file
    :param handle_images: whether or not to extract, download and parse images within the downloaded file
    :return: the filename of the written file
    """

    # assign a unique UUID4 to be the filename
    filename = '{0}.{1}'.format(uuid4(), extension)

    # set the path to the article's sub-folder
    path = os.path.join(settings.BASE_DIR, 'files', 'articles', str(article.id))

    # create the sub-folder structure if needed
    if not os.path.exists(path):
        os.makedirs(path, 0o0775)

    # write the file to disk
    with open(os.path.join(path, filename), 'wb') as f:
        # process any images if instructed
        if handle_images:
            contents = fetch_images_and_rewrite_xml_paths(base, root, contents, article, user)

        if isinstance(contents, str):
            contents = bytes(contents, 'utf8')

        f.write(contents)

    return filename


def add_file(file_mime, extension, description, owner, filename, article, galley=True, thumbnail=False):
    """ Add a file to the File model in core. Saves a file to the database affiliated with an article.

    :param file_mime: the MIME type of the file. Used in serving the file back to users
    :param extension: the extension of the file
    :param description: a description of the file
    :param owner: the user who owns the file
    :param filename: the filename
    :param article: the article with which the file is associated
    :param galley: whether or not this is a galley file
    :param thumbnail: whether or not this is a thumbnail
    :return: the new File object
    """

    # create a new File object with the passed parameters
    new_file = core_models.File(
        mime_type=file_mime,
        original_filename='file.{0}'.format(extension),
        uuid_filename=filename,
        label=extension.upper(),
        description=description,
        owner=owner,
        is_galley=galley,
        privacy='public',
        article_id=article.pk
    )

    new_file.save()

    if thumbnail:
        article.thumbnail_image_file = new_file
        article.save()
        return new_file

    # if it is a galley, add to the list of manuscript files. Otherwise, add to the list of data files.
    if galley:
        article.manuscript_files.add(new_file)
        core_models.Galley.objects.create(
            article=article,
            file=new_file,
            is_remote=False,
            label=new_file.label,
            type=extension,
        )
    else:
        article.data_figure_files.add(new_file)

    article.save()

    return new_file


def get_soup(soup_object, field_name, default=None):
    """ Parses a soup object and returns field_name if found, otherwise default

    :param soup_object: the BeautifulSoup object to parse
    :param field_name: the name of the field to look for
    :param default: the default to return if it isn't found
    :return: a default value to return if the soup_object is None
    """
    if soup_object:
        return soup_object.get(field_name, None)
    else:
        return default


def parse_url(url):
    """ Parses a URL into a well-formed and navigable format

    :param url: the URL to parse
    :return: the formatted URL
    """
    return '{uri.scheme}://{uri.netloc}/'.format(uri=urlparse(url))


def fetch_page(url):
    """ Fetches a remote page and returns a BeautifulSoup object

    :param url: the URL to fetch
    :return: a BeautifulSoup object
    """
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    resp, mime = utils_models.ImportCacheEntry.fetch(url=url)
    return BeautifulSoup(resp, 'lxml-xml')


def extract_and_check_doi(soup_object):
    """
    Extracts a DOI from a soup_object of a page and returns a Tuple of the DOI and whether we already have it in the
    local journal.

    :param soup_object: a BeautifulSoup object of a page
    :return: a tuple of the doi and whether it exists locally (a boolean)
    """
    # see whether there's a DOI and, most importantly, whether it's a duplicate
    doi = get_soup(soup_object.find('meta', attrs={'name': 'citation_doi'}), 'content')

    if doi:
        identifier = identifiers_models.Identifier.objects.filter(id_type='doi', identifier=doi)

        if identifier:
            print('DOI {0} already imported. Skipping.'.format(doi))
            return doi, True
        else:
            return doi, False
    else:
        return doi, False


def get_author_info(soup_object):
    """ Extract authors, emails, and institutional affiliation from a BeautifulSoup object.

    :param soup_object: a BeautifulSoup object of a page
    :return: a tuple of authors, emails, institutions and a boolean of whether we have emails for all authors
    """
    authors = soup_object.findAll('meta', attrs={'name': 'citation_author'})
    if not authors:
        authors = soup_object.findAll('meta', attrs={'name': 'citation_authors'})

    emails = soup_object.findAll('meta', attrs={'name': 'citation_author_email'})
    institutions = soup_object.findAll('meta', attrs={'name': 'citation_author_institution'})

    mismatch = len(authors) != len(emails)

    if mismatch:
        print('Mismatch in number of authors, emails and institutions added. This article will not be '
              'correctly attributed.')

    return authors, emails, institutions, mismatch


def get_pdf_url(soup_object):
    """
    Returns the value of the meta tag where the name attribute is citation_pdf_url from a BeautifulSoup object of a
    page.

    :param soup_object: a BeautifulSoup object of a page
    :return: a string of the PDF URL
    """
    pdf = get_soup(soup_object.find('meta', attrs={'name': 'citation_pdf_url'}), 'content')

    if pdf:
        pdf = pdf.replace('article/view/', 'article/viewFile/')

    return pdf


def get_dates(soup_object, date_published_iso=False, date_submitted_iso=False):
    """ Extracts publication dates from a BeautifulSoup object of a page.

    :param soup_object: a BeautifulSoup object of a page
    :param date_published_iso: whether or not the date_published is in an ISO date format
    :param date_submitted_iso: whether or not the date_submitted is in an ISO date format
    :return: a tuple of the date published and the date submitted
    """
    pubbed = get_soup(soup_object.find('meta', attrs={'name': 'citation_publication_date'}), 'content')

    if not pubbed or pubbed == '':
        pubbed = get_soup(soup_object.find('meta', attrs={'name': 'DC.Date.issued'}), 'content')

    date_published = parse_date(pubbed, date_published_iso)

    date_submitted = parse_date(get_soup(soup_object.find('meta', attrs={'name': 'DC.Date.dateSubmitted'}), 'content'),
                                date_submitted_iso)

    return date_published, date_submitted


def create_new_article(date_published, date_submitted, journal, soup_object, user):
    """ Create a new article in the database.

    :param date_published: the date the article was published
    :param date_submitted: the date the article was submitted
    :param journal: the journal to which the article belongs
    :param soup_object: the BeautifulSoup object from which to extract the remaining fields
    :param user: the user to be set as the owner of this article
    :return: a tuple of a dictionary information about the article and the new article object
    """

    article_dict = {
        'title': get_soup(soup_object.find('meta', attrs={'name': 'DC.Title'}), 'content'),
        'abstract': get_soup(soup_object.find('meta', attrs={'name': 'DC.Description'}), 'content', ''),
        'language': get_soup(soup_object.find('meta', attrs={'name': 'DC.Language'}), 'content'),
        'date_published': date_published,
        'date_submitted': date_submitted,
        'journal': journal,
        'owner': user,
        'stage': "Published",
        'current_step': 5,
        'page_numbers': get_soup(soup_object.find('meta', attrs={'name': 'DC.Identifier.pageNumber'}), 'content', ''),
        'is_import': True,
    }

    new_article = submission_models.Article.objects.create(**article_dict)

    return article_dict, new_article


def set_article_attributions(authors, emails, institutions, mismatch, article):
    """ Set author, email, and institution information on an article

    :param authors: the authors of the article
    :param emails: the authors' emails
    :param institutions: the authors' institutions
    :param mismatch: whether or not there is a mismatch between the number of authors and institutions
    :param article: the article on which this attribution information should be set
    :return: None
    """
    fetch_emails = not mismatch

    for idx, val in enumerate(authors):
        author_name = get_soup(val, 'content')

        if ',' in author_name:
            split_author = author_name.split(', ', 1)
            print(split_author)
            author_name = '{0} {1}'.format(split_author[1], split_author[0])
            print(author_name)

        if fetch_emails:
            email = get_soup(emails[idx], 'content')
        else:
            # if there are a bad number of emails, we will automatically generate one
            email = utils_shared.generate_password(16)
            email = u"{0}@journal.org".format(email)

        if len(authors) == len(institutions):
            institution = get_soup(institutions[idx], 'content')
        else:
            # if no institution, simply set to blank
            institution = ''

        # add an account for this new user
        account = core_models.Account.objects.filter(email=email)

        if account is not None and len(account) > 0:
            account = account[0]
            print("Found account for {0}".format(email))
        else:
            print("Didn't find account for {0}. Creating.".format(email))
            account = core_models.Account.objects.create(email=email, username=uuid4(), institution=institution,
                                                         first_name=' '.join(author_name.split(' ')[:-1]),
                                                         last_name=author_name.split(' ')[-1])
            account.save()

        if account:
            article.authors.add(account)
            account.snapshot_self(article)


def set_article_section(article, soup_object, element='h4', attributes=None, default='Articles'):
    """ Set an article to a specific section

    :param article: the article in question
    :param soup_object: a BeautifulSoup object of a page from which to extract section information
    :param element: optional element name (string) from which to grab the article section
    :param attributes: optional dictionary of attributes to search for article section
    :param default: the name of the default section (string)
    :return: None
    """

    # set the default section name here
    if attributes is None:
        attributes = {'class': 'main-color-text'}

    section_name = default

    # attempt to extract a section title
    try:
        section_name = soup_object.find(element, attrs=attributes).getText().strip()
    except AttributeError:
        pass

    # either attribute the section or notify the user that we are using the default
    if section_name and section_name != '':
        print('Adding article to section {0}'.format(section_name))

        section, created = submission_models.Section.objects.language('en').get_or_create(journal=article.journal, name=section_name)
        article.section = section
    else:
        print('No section information found. Reverting to default of "Articles"')


def set_article_issue_and_volume(article, soup_object, date_published):
    """ Set the article's issue and volume

    :param article: the article in question
    :param soup_object: a BeautifulSoup object of a page
    :param date_published: the date the article was published
    :return: None
    """
    issue = int(get_soup(soup_object.find('meta', attrs={'name': 'citation_issue'}), 'content', 0))
    volume = int(get_soup(soup_object.find('meta', attrs={'name': 'citation_volume'}), 'content', 0))

    if issue == 0:
        issue = int(get_soup(soup_object.find('meta', attrs={'name': 'DC.Source.Issue'}), 'content', 0))
    if volume == 0:
        volume = int(get_soup(soup_object.find('meta', attrs={'name': 'DC.Source.Volume'}), 'content', 0))

    new_issue, created = journal_models.Issue.objects.get_or_create(journal=article.journal, issue=issue, volume=volume)
    new_issue.date = date_published

    article.issues.add(new_issue)

    if created:
        new_issue.save()
        print("Created a new issue ({0}:{1}, {2})".format(volume, issue, date_published))


def set_article_galleys(domain, galleys, article, url, user):
    """ Attach a set of remote galley files to the local article

    :param domain: the formatted domain object for the remote file
    :param galleys: a dictionary of named galley URLs to harvest
    :param article: the article to which to attach the galleys
    :param url: the URL of the remote galley
    :param user: the user who should own the new file
    :return: None
    """
    for galley_name, galley in galleys.items():
        if galley:
            if galley_name == 'PDF' or galley_name == 'XML':
                handle_images = True if galley_name == 'XML' else False
                filename, mime = fetch_file(domain, galley, url, galley_name.lower(), article, user,
                                            handle_images=handle_images)
                add_file('application/{0}'.format(galley_name.lower()), galley_name.lower(),
                         'Galley {0}'.format(galley_name), user, filename, article)
            else:
                # assuming that this is HTML, which we save to disk rather than fetching
                handle_images = True if galley_name == 'HTML' else False
                filename = save_file(domain, galley, url, galley_name.lower(), article, user,
                                     handle_images=handle_images)
                add_file('text/{0}'.format(galley_name.lower()), galley_name.lower(),
                         'Galley {0}'.format(galley_name), user, filename, article)


def set_article_identifier(doi, article):
    """ Save an identifier to the article

    :param doi: the DOI to save
    :param article: the article on which to act
    :return: None
    """
    if doi:
        identifier = identifiers_models.Identifier.objects.create(id_type='doi', identifier=doi, article=article)
        identifier.save()
        print("Article imported with ID: {0}".format(doi))
    else:
        print("Article imported with ID: {0}".format(article.id))


def fetch_page_and_check_if_exists(url):
    """ Fetch a remote URL and check if the DOI already exists

    :param url: the URL of the remote page
    :return: tuple of whether the DOI already exists locally, the DOI, the formatted domain, and the BeautifulSoup
    object of the page
    """

    domain = parse_url(url)
    soup_object = fetch_page(url)
    doi, already_exists = extract_and_check_doi(soup_object)

    return already_exists, doi, domain, soup_object


def get_and_set_metadata(journal, soup_object, user, date_published_iso, date_submitted_iso):
    """ Fetch article metadata and attach it to the article

    :param journal: the journal to which the article should belong
    :param soup_object: a BeautifulSoup object of the page
    :param user: the owner user to whom the article and files should be assigned
    :param date_published_iso: whether or not the date published field is in ISO date format
    :param date_submitted_iso: date_published_iso: whether or not the date submitted field is in ISO date format
    :return: the new article
    """
    authors, emails, institutions, mismatch = get_author_info(soup_object)

    date_published, date_submitted = get_dates(soup_object, date_published_iso=date_published_iso,
                                               date_submitted_iso=date_submitted_iso)

    article_dict, new_article = create_new_article(date_published, date_submitted, journal, soup_object, user)

    set_article_attributions(authors, emails, institutions, mismatch, new_article)
    set_article_section(new_article, soup_object)
    set_article_issue_and_volume(new_article, soup_object, date_published)

    return new_article


def set_article_galleys_and_identifiers(doi, domain, galleys, article, url, user):
    """ Set the galleys and identifiers on an article

    :param doi: the DOI
    :param domain: the formatted URL domain string
    :param galleys: the galleys dictionary to parse
    :param article: the article in question
    :param url: the URL of the remote galley
    :param user: the user who should own newly ingested material
    :return: None
    """
    set_article_galleys(domain, galleys, article, url, user)
    set_article_identifier(doi, article)


def fetch_email_from_href(a_soup):
    href = urllib.parse.unquote(a_soup.attrs['href'])

    email_regex = r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)"

    email = re.search(email_regex, href)

    if email:
        return email.group(1)
    else:
        return None


def parse_title_data(soup):
    title_info = dict()
    tables = soup.find("div", {"id": "titleAndAbstract"}).findAll("table")

    # NB there should only be one here
    for table in tables:
        rows = table.find_all("tr")

        cells_title = rows[0].find_all("td")
        title_info['title'] = cells_title[1].get_text().strip()

        cells_abstract = rows[1].find_all("td")
        title_info['abstract'] = cells_abstract[1].get_text().strip()

    return title_info


def parse_author_data(soup):
    authors = list()
    tables = soup.find("div", {"id": "authors"}).findAll("table")

    for table in tables:
        author_dict = dict()
        for row in table.find_all("tr"):
            cells = row.find_all("td")

            try:
                cell_0 = cells[0].get_text().strip()
                cell_1 = cells[1].get_text().strip()

                a_elem = cells[1].find("a")

                if a_elem:
                    email = fetch_email_from_href(a_elem)
                    if email:
                        author_dict['email'] = email

                if cell_0 == 'Name' and author_dict:
                    authors.append(author_dict)
                    author_dict = dict()

                author_dict[cell_0] = cell_1
            except IndexError:
                pass

        authors.append(author_dict)

    return authors


def parse_indexing_data(soup):
    indexing_info = dict()
    tables = soup.find("div", {"id": "indexing"}).findAll("table")

    for table in tables:
        rows = table.find_all("tr")

        cells_keywords = rows[1].find_all("td")
        cells_language = rows[2].find_all("td")

        indexing_info['keywords'] = cells_keywords[1].get_text().strip().split(',')
        indexing_info['language'] = cells_language[1].get_text().strip()

    return indexing_info


def get_jms_article_status(soup):
    """
        Returns an article status
        :param soup:
        :return:
        """
    tables = soup.find("div", {"id": "editorDecision"}).findAll("table")

    for table in tables:
        author_dict = dict()
        for row in table.find_all("tr"):
            cells = row.find_all("td")

            try:
                cell_0 = cells[0].get_text().strip()
                cell_1 = cells[1].get_text().strip()

                if(cell_0 == 'Decision'):
                    cell_1 = cell_1.split('|')[len(cell_1.split('|'))-1]

                    date_regex = '(\d{4}\-\d{2}\-\d{2},\s\d{2}\:\d{2})'
                    date_time = dateparser.parse(re.search(date_regex, cell_1).groups(1)[0])

                    text_regex = '([^\d]+)'
                    text = re.search(text_regex, cell_1).groups(1)[0].strip()

                    outcome = submission_models.STAGE_ASSIGNED

                    if text == 'Resubmit for Review':
                        outcome = submission_models.STAGE_UNDER_REVISION
                    if text == 'Revisions Required':
                        outcome = submission_models.STAGE_UNDER_REVISION
                    if text == 'Accept Submission':
                        outcome = submission_models.STAGE_ACCEPTED
                    if text == 'Decline Submission':
                        outcome = submission_models.STAGE_REJECTED

                    return outcome, date_time

            except IndexError:
                pass

    return None


def get_files(soup):
    """
    Finds all of he files on the review page and pulls the latest version.
    :param soup:
    :return:
    """
    files = soup.findAll("a", {"class": "file"})
    file_dict = dict()
    return_dict = {'supplementary_files': []}

    for file in files:
        file_parts = file.get_text().split('-')
        file_id = file_parts[1]
        file_type = file_parts[3].split('.')[0]

        if file_type in ['RV', 'ED', 'AV']:
            file_dict[file_id] = file.get('href')
        elif file_type == 'SP':
            return_dict['supplementary_files'].append(file.get('href'))

    newest_file = max(file_dict, key=int)

    return_dict['file'] = file_dict[newest_file]

    return return_dict


def parse_recommend(recommendation_text):
    recommendation = recommendation_text.split('\n')[0]
    try:
        date = dateparser.parse(re.search('(\d{4}\-\d{2}\-\d{2},\s\d{2}\:\d{2})', recommendation_text).groups(1)[0])
    except:
        date = None
    return recommendation, date


def get_peer_reviewers(soup):
    review_blocks = soup.find("div", {"id": "peerReview"}).findAll("div")
    reviewer_list = list()

    for review in review_blocks:
        reviewer_dict = {}
        tables = review.findAll("table")

        # Get the name out of table 1
        reviewer_dict['name'] = tables[0].findAll('td')[1].get_text()

        table_trs = tables[1].findAll('tr')
        date_tds = table_trs[1].find('table').findAll('td')

        reviewer_dict['date_requested'] = dateparser.parse(date_tds[4].get_text().strip())
        reviewer_dict['date_accepted'] = dateparser.parse(date_tds[5].get_text().strip()) if date_tds[5].get_text() else None
        reviewer_dict['date_due'] = dateparser.parse(date_tds[6].get_text().strip()) if date_tds[6].get_text() else None

        recommendation_tds = table_trs[4].findAll('td')
        reviewer_dict['recommendation'], reviewer_dict['recommendation_date_time'] = parse_recommend(recommendation_tds[1].get_text(strip=True))

        reviewer_list.append(reviewer_dict)
        
    return reviewer_list


def get_user_profile(soup):
    """
    Fetches user info from a Ubiquity Press profile
    :param soup: BeautifulSoup object
    :return: A dictionary
    """
    authors = list()
    tables = soup.find("div", {"id": "profile"}).findAll("table")

    for table in tables:
        author_dict = dict()
        for row in table.find_all("tr"):
            cells = row.find_all("td")

            try:
                cell_0 = cells[0].get_text().strip()
                cell_1 = cells[1].get_text().strip()

                a_elem = cells[1].find("a")

                if a_elem:
                    email = fetch_email_from_href(a_elem)
                    if email:
                        author_dict['email'] = email

                if cell_0 == 'Name' and author_dict:
                    authors.append(author_dict)
                    author_dict = dict()

                author_dict[cell_0] = cell_1
            except IndexError:
                pass

        authors.append(author_dict)

    return authors


def get_metadata(soup):
    """
    Fetches title, authors etc for an in review article
    :param soup: BeautifulSoup object
    :return: A dictionary
    """
    authors = parse_author_data(soup)
    titles = parse_title_data(soup)
    indexing = parse_indexing_data(soup)

    print(authors)
    print(titles)
    print(indexing)

    return {'authors': authors, 'titles': titles, 'indexing': indexing}


