import os
from datetime import datetime
import hashlib
from urllib.parse import urlparse
from uuid import uuid4
import requests
from bs4 import BeautifulSoup
import urllib
import re
from pathlib import Path

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
from utils.logger import get_logger

logger = get_logger(__name__)


def fetch_images_and_rewrite_xml_paths(base, root, contents, article, user, galley_name="XML"):
    """Download images from an XML or HTML document and rewrite the new galley to point to the correct source.

    :param base: a base URL for the remote journal install e.g. http://www.myjournal.org
    :param root: the root page (i.e. the article that we are grabbing from) e.g. /article/view/27
    :param contents: the current page's HTML or XML
    :param article: the new article to which this download should be attributed
    :param user: the user who will be assigned as the file owner of any downloaded file
    :return: a string of the rewritten XML or HTML
    """

    # create a BeautifulSoup instance of the page's HTML or XML
    if galley_name == "HTML":
        parser = "html.parser"
    else:
        parser = "lxml"
    soup = BeautifulSoup(contents, parser)

    # add element:attribute properties here for images that should be downloaded and have their paths rewritten
    # so 'img':'src' means look for elements called 'img' with an attribute 'src'
    elements = {
        'img': 'src',
        'graphic': 'xlink:href'
    }

    # iterate over all found elements
    for element, attribute in elements.items():
        images = soup.findAll(element)

        # iterate over all found elements of each type in the elements dictionary
        for idx, val in enumerate(images):

            # attempt to pull a URL from the specified attribute
            url = get_soup(val, attribute)

            if url:
                url_to_use = url

                # this is a Ubiquity Press-specific fix to rewrite the path so that we don't hit OJS's dud backend
                if not url.startswith('/') and not url.startswith('http'):
                    # Resolve article redirects before building image URLs
                    real_root = requests.head(root, allow_redirects=True).url
                    url_to_use = real_root.replace('/article/view', '/articles') + '/' + url

                #guess extension from url
                suffixes = Path(url_to_use).suffixes
                if suffixes:
                    extension = "".join(suffixes)
                else:
                    extension = ""

                # download the image file
                filename, mime = fetch_file(base, url_to_use, root, extension, article, user, handle_images=False)

                # determine the MIME type and slice the first open bracket and everything after the comma off
                mime = mime.split(',')[0][1:].replace("'", "")

                # store this image in the database affiliated with the new article
                new_file = add_file(mime, extension, 'Galley image', user, filename, article, False)
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


def fetch_file(base, url, root, extension, article, user, handle_images=False, auth_file=None):
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

    if not settings.SILENT_IMPORT_CACHE:
        print('Fetching {0}'.format(url))

    # imitate headers from a browser to avoid being blocked on some installs
    if auth_file:
        resp, mime = utils_models.ImportCacheEntry.fetch(url, up_auth_file=auth_file, up_base_url=base)
    else:
        resp, mime = utils_models.ImportCacheEntry.fetch(url=url)

    # If the function is not passed an extension, try to guess what it should be.

    if not extension:
        extension = utils_shared.guess_extension(mime)

    # set the filename to a unique UUID4 identifier with the passed file extension
    filename = '{0}.{1}'.format(uuid4(), extension.lstrip("."))

    # set the path to save to be the sub-directory for the article
    path = os.path.join(settings.BASE_DIR, 'files', 'articles', str(article.id))

    # create the sub-folders as necessary
    if not os.path.exists(path):
        os.makedirs(path, 0o0775)

    # intercept the request if we need to parse this as HTML or XML with images to rewrite
    if handle_images:
        try:
            resp = resp.decode()
            resp = fetch_images_and_rewrite_xml_paths(base, root, resp, article, user)
        except UnicodeDecodeError:
            logger.warning("Cant extract images from %s" % url)

    if isinstance(resp, str):
        resp = bytes(resp, 'utf-8')

    with open(os.path.join(path, filename), 'wb') as f:
        if not settings.SILENT_IMPORT_CACHE:
            print("Writing file {0} as binary".format(os.path.join(path, filename)))
        f.write(resp)

    # return the filename and MIME type
    return filename, mime


def save_file(base, contents, root, extension, article, user, handle_images=False, galley_name="XML"):
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
            contents = fetch_images_and_rewrite_xml_paths(base, root, contents, article, user, galley_name)

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

    if extension.startswith('.'):
        original_filename = 'file{0}'.format(extension)
    else:
        original_filename = 'file.{0}'.format(extension)

    new_file = core_models.File(
        mime_type=file_mime,
        original_filename=original_filename,
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
    if "/html" in mime:
        parser = "html"
    else:
        parser = "lxml-xml"
    return BeautifulSoup(resp, parser)


def extract_and_check_doi(soup_object):
    """
    Extracts a DOI from a soup_object of a page and returns a Tuple of the DOI and whether we already have it in the
    local journal.

    :param soup_object: a BeautifulSoup object of a page
    :return: a tuple of the doi and the identified item or False
    """
    # see whether there's a DOI and, most importantly, whether it's a duplicate
    doi = get_soup(soup_object.find('meta', attrs={'name': 'citation_doi'}), 'content')
    found = False

    if doi:
        try:
            identifier = identifiers_models.Identifier.objects.get(
                id_type='doi',
                identifier=doi
            )
            found = identifier.article or False
        except identifiers_models.Identifier.DoesNotExist:
            pass

    return doi, found


def get_citation_info(soup_object):
    citations = soup_object.find_all('div', attrs={"class": "citation-popup"})
    if citations:
        return citations[0].text
    return None


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
    import html
    abstract_html = get_soup(soup_object.find('meta', attrs={'name': 'DC.Description'}), 'content', ''),
    abstract = html.unescape(abstract_html)

    article_dict = {
        'title': get_soup(soup_object.find('meta', attrs={'name': 'DC.Title'}), 'content'),
        'abstract': abstract[0],
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
    if not article_dict.get("title"):
        article_dict["title"] = "# No Title found #"

    new_article = submission_models.Article.objects.create(**article_dict)

    return article_dict, new_article


def set_article_attributions(authors, emails, institutions, mismatch, article, citation=None):
    """ Set author, email, and institution information on an article

    :param authors: the authors of the article
    :param emails: the authors' emails
    :param institutions: the authors' institutions
    :param mismatch: whether or not there is a mismatch between the number of authors and institutions
    :param article: the article on which this attribution information should be set
    :param citation: The citation string, helps distinguish conjuntions from middle names
    :return: None
    """
    fetch_emails = not mismatch

    for idx, val in enumerate(authors):
        author_name = get_soup(val, 'content')

        if ',' in author_name:
            split_author = author_name.split(', ', 1)
            author_name = '{0} {1}'.format(split_author[1], split_author[0])

        if fetch_emails:
            email = get_soup(emails[idx], 'content')
            if email == "journal@openlibhums.org":
                # Generate Janeway compatible dummy email
                email = utils_shared.generate_password(16)
                email = u"{0}@{1}".format(email, settings.DUMMY_EMAIL_DOMAIN)
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
        account = core_models.Account.objects.filter(email__iexact=email)
        parsed_name = parse_author_names(author_name, citation)

        if account is not None and len(account) > 0:
            account = account[0]
            print("Found account for {0}".format(email))
        else:
            print("Didn't find account for {0}. Creating.".format(email))
            logger.debug("%s\t\t-> %s" % (author_name, parsed_name))
            account = core_models.Account.objects.create(
                email=email,
                username=uuid4(),
                institution=institution,
                first_name=parsed_name["first_name"],
                last_name=parsed_name["last_name"],
                middle_name=parsed_name["middle_name"],
            )
            account.save()

        if account:
            article.authors.add(account)
            o, c = submission_models.ArticleAuthorOrder.objects.get_or_create(
                article=article,
                author=account,
                defaults={'order': article.next_author_sort()},
            )
            # Copy behaviour of snapshot_self, some authors might have a
            # shared dummy email address.
            f, created = submission_models.FrozenAuthor.objects.get_or_create(
                **{
                    'article': article,
                    'first_name': parsed_name["first_name"],
                    'middle_name': parsed_name["middle_name"],
                    'last_name': parsed_name["last_name"],
                    'institution': institution,
                    'order': o.order,
                    'defaults': {"author": account},

                },
            )



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
    issue_type = journal_models.IssueType.objects.get(
        journal=article.journal,
        code="issue",
    )
    issue = get_soup(soup_object.find('meta', attrs={'name': 'citation_issue'}), 'content', 0)
    volume = int(get_soup(soup_object.find('meta', attrs={'name': 'citation_volume'}), 'content', 0))

    # Try DC tags
    if not issue:
        dc_issue = get_soup(soup_object.find('meta', attrs={'name': 'DC.Source.Issue'}), 'content', "")
    if not volume:
        dc_volume = get_soup(soup_object.find('meta', attrs={'name': 'DC.Source.Volume'}), 'content', "")
        if dc_volume.isdigit():
            volume = int(dc_volume)

    new_issue, created = journal_models.Issue.objects.get_or_create(
        journal=article.journal,
        issue=issue,
        volume=volume,
        defaults={
            "issue_type": issue_type,
            "date": date_published,
        },
    )
    article.issues.add(new_issue)

    if created:
        new_issue.save()
        log_string = "Created a new issue ({0}:{1}, {2})".format(
            volume, issue, date_published)
        logger.info(log_string)


def set_article_keywords(article, soup_object):
    keyword_string = (get_soup(
        soup_object.find('meta', attrs={'name': 'citation_keywords'}),
        'content',
    ))
    if keyword_string:
        for i, word in enumerate(keyword_string.split(";")):
            if word:
                keyword, created = submission_models.Keyword.objects \
                    .get_or_create(word=word.lstrip())
                submission_models.KeywordArticle.objects.update_or_create(
                    article=article,
                    keyword=keyword,
                    defaults = {"order": i},
                )


def set_article_galleys(domain, galleys, article, url, user):
    """ Attach a set of remote galley files to the local article

    :param domain: the formatted domain object for the remote file
    :param galleys: a dictionary of named galley URLs to harvest
    :param article: the article to which to attach the galleys
    :param url: the URL of the remote galley
    :param user: the user who should own the new file
    :return: None
    """
    article.galley_set.all().delete()
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
                                     handle_images=handle_images, galley_name=galley_name)
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

    citation = get_citation_info(soup_object)
    set_article_attributions(authors, emails, institutions, mismatch, new_article, citation)
    set_article_section(new_article, soup_object)
    set_article_issue_and_volume(new_article, soup_object, date_published)
    set_article_keywords(new_article, soup_object)

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


def fetch_email_from_href(a_soup):
    href = urllib.parse.unquote(a_soup.attrs['href'])

    email_regex = r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)"

    email = re.search(email_regex, href)

    if email:
        return email.group(1)
    else:
        return None


def parse_author_names(author, citation=None):
    """ Parses parts of the name from input string checking against citation

    Can distinguish middle names from multi word last_names
    :param author: A single string containing the author's full name
    :param citation: The citation string where this author appears
    :return: A dict of name type to name value
    """
    names = author.split(" ")
    first = last = middle = None
    if not citation:
        first = " ".join(names[:-1])
        last = names[-1]
    elif len(names) == 1:
        last = names[0]
    elif len(names) == 2:
        first, last = names
    elif len(names) > 2:
        first = names[0]
        for i, name in enumerate(names[1:]):
            # Check if any substring is in the citation
            start_idx = names.index(name)
            if len(names[start_idx:]) < 2:
                last = name
            else:
                guess = " ".join(names[start_idx:])
                if guess in citation:
                    last = guess
                    middle = " ".join(names[1:start_idx]) or None
                    break
                else:
                    middle = name
    return {
        "first_name": first,
        "middle_name": middle,
        "last_name": last,
    }


SEED_KEYS = [
    "First Name", "Middle Name", "Last Name", "Affiliation", "Country"
]
def generate_dummy_email(profile_dict):
    seed = sum(profile_dict.get(key, "") for key in SEED_KEYS)
    hashed = hashlib.md5(str(seed).encode("utf-8")).hexdigest()
    return "{0}@{1}".format(hashed, settings.DUMMY_EMAIL_DOMAIN)
