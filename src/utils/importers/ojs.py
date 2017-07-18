from bs4 import BeautifulSoup

from utils.importers import shared


# note: URL to pass for import is http://journal.org/journal/oai/


def import_article(journal, user, url):
    """ Import an Open Journal Systems article.

    :param journal: the journal to import to
    :param user: the user who will own the file
    :param url: the URL of the article to import
    :return: None
    """

    # retrieve the remote page and establish if it has a DOI
    already_exists, doi, domain, soup_object = shared.fetch_page_and_check_if_exists(url)

    if already_exists:
        # if here then this article has already been imported
        return

    # fetch basic metadata
    new_article = shared.get_and_set_metadata(journal, soup_object, user, False, False)

    # get PDF and XML/HTML galleys
    pdf = shared.get_pdf_url(soup_object)

    html = shared.get_soup(soup_object.find('meta', attrs={'name': 'citation_fulltext_html_url'}), 'content')
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/39.0.2171.95 Safari/537.36'}
    if html:
        html = shared.requests.get(html, headers=headers)

        html_contents = BeautifulSoup(html.text, "lxml")
        html_contents = html_contents.find('div', attrs={'id': 'content'})

        if html_contents:
            html_contents = BeautifulSoup(html_contents.decode_contents(formatter=None), "lxml")
            html_contents = html_contents.find('body')
            html_contents = html_contents.decode_contents(formatter=None)
    else:
        html_contents = None

    # attach the galleys to the new article
    galleys = {
        'PDF': pdf,
    }

    if html_contents:
        galleys['HTML'] = html_contents

    shared.set_article_galleys_and_identifiers(doi, domain, galleys, new_article, url, user)

    # save the article to the database
    new_article.save()


def import_oai(journal, user, soup):
    """ Initiate an OAI import on an Open Journal Systems journal.

    :param journal: the journal to import to
    :param user: the user who will own imported articles
    :param soup: the BeautifulSoup object of the OAI feed
    :return: None
    """
    identifiers = soup.findAll('dc:identifier')

    for identifier in identifiers:
        if identifier.contents[0].startswith('http'):
            print('Parsing {0}'.format(identifier.contents[0]))

            import_article(journal, user, identifier.contents[0])
