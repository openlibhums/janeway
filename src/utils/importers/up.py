import hashlib
import re
import uuid
import os
import requests
from bs4 import BeautifulSoup
import json
from dateutil import parser as dateparser
from urllib.parse import urlparse

from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone
from django.utils.html import strip_tags
from django.contrib.contenttypes.models import ContentType

from utils.importers import shared
from submission import models
from journal import models as journal_models
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from utils import models as utils_models, setting_handler
from core import models as core_models, files as core_files
from review import models as review_models
from utils.logger import get_logger
from cms import models as cms_models

logger = get_logger(__name__)

# note: URL to pass for import is http://journal.org/jms/index.php/up/oai/


def get_thumbnails_url(url):
    """ Extract thumbnails URL from a Ubiquity Press site.

    :param url: the base URL of the journal
    :return: the thumbnail URL for this journal
    """
    logger.info("Extracting thumbnails URL.")

    section_filters = ["f=%d" % i for i in range(1,100)]
    flt = "&".join(section_filters)
    url_to_use = url + '/articles/?' + flt + '&order=date_published&app=100000'
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


def import_article(journal, user, url, thumb_path=None, update=False):
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

    if already_exists and update:
        article = already_exists
    elif already_exists:
        return
    else:
        article = shared.get_and_set_metadata(journal, soup_object, user, False, True)

    # try to do a license lookup
    pattern = re.compile(r'creativecommons')
    license_tag = soup_object.find(href=pattern)
    license_object = models.Licence.objects.filter(url=license_tag['href'].replace('http:', 'https:'), journal=journal)

    if len(license_object) > 0 and license_object[0] is not None:
        license_object = license_object[0]
        logger.info("Found a license for this article: {0}".format(
            license_object.short_name))
    else:
        license_object = models.Licence.objects.get(name='All rights reserved', journal=journal)
        logger.warning(
            "Did not find a license for this article. Using: {0}".format(
                license_object.short_name
            )
        )

    article.license = license_object

    # determine if the article is peer reviewed
    peer_reviewed = soup_object.find(name='a', text='Peer Reviewed') is not None
    logger.debug("Peer reviewed: {0}".format(peer_reviewed))

    article.peer_reviewed = peer_reviewed

    # get PDF and XML galleys
    pdf = shared.get_pdf_url(soup_object)

    # rip XML out if found
    pattern = re.compile('.*?XML.*')
    xml = soup_object.find('a', text=pattern)
    html = None

    if xml:
        logger.info("Ripping XML")
        xml = xml.get('href', None).strip()
    else:
        # looks like there isn't any XML
        # instead we'll pull out any div with an id of "xml-article" and add as an HTML galley
        logger.info("Ripping HTML")
        html = soup_object.find('div', attrs={'id': 'xml-article'})

        if html:
            html = str(html.contents[0])

    # attach the galleys to the new article
    galleys = {
        'PDF': pdf,
        'XML': xml,
        'HTML': html
    }
    shared.set_article_galleys(domain, galleys, article, url, user)
    if not already_exists:
        # The code below is not safe for updates
        shared.set_article_identifier(doi, article)
    # fetch thumbnails
    if thumb_path is None:
        parsed_url = urlparse(url)
        base_url = parsed_url._replace(path="").geturl()
        thumb_path = get_thumbnails_url(base_url)

    if thumb_path is not None:
        logger.info("Attempting to assign thumbnail.")

        if url.endswith("/"):
            url = url[:-1]
        final_path_element = url.split('/')[-1]
        id_regex = re.compile(r'.*?(\d+)')
        matches = id_regex.match(final_path_element)
        try:
            article_id = matches.group(1)

            logger.info("Determined remote article ID as: {0}".format(article_id))
            logger.info("Thumbnail path: {thumb_path}, URL: {url}".format(
                thumb_path=thumb_path, url=url))

            filename, mime = shared.fetch_file(
                domain,
                thumb_path + "/" + article_id, "",
                'graphic',
                article, user,
            )
            shared.add_file(
                mime, 'graphic', 'Thumbnail', user, filename, article,
                thumbnail=True,
            )
        except AttributeError:
            logger.error("Unable to import thumbnail: No id in %s" % url)
        except Exception as e:
            logger.warning("Unable to import thumbnail: %s" % e)

    article.save()

    # lookup stats
    stats = soup_object.findAll('div', {'class': 'stat-number'})

    try:
        if stats and (not already_exists or update):
            from metrics import models as metrics_models
            views = stats[0].contents[0]
            if len(stats) > 1:
                downloads = stats[1].contents[0]
            else:
                downloads = 0

            o, _ = metrics_models.HistoricArticleAccess.objects.get_or_create(
                article=article)

            o.downloads = downloads
            o.views=views
            o.save()
    except (IndexError, AttributeError):
        logger.info("No article metrics found")

    return article


def import_oai(journal, user, soup, domain, update=False):
    """ Initiate an OAI import on a Ubiquity Press journal.

        :param journal: the journal to import to
        :param user: the user who will own imported articles
        :param soup: the BeautifulSoup object of the OAI feed
        :param domain: the domain of the journal (for extracting thumbnails)
        :return: None
        """

    thumb_path = get_thumbnails_url(domain)

    identifiers = soup.findAll('dc:identifier')

    for identifier in identifiers:
        # rewrite the phrase /jms in Ubiquity Press OAI feeds to get version with
        # full and proper email metadata
        identifier.contents[0] = identifier.contents[0].replace('/jms', '')
        if identifier.contents[0].startswith('http'):
            logger.info('Parsing {0}'.format(identifier.contents[0]))

            import_article(
                journal, user, identifier.contents[0], thumb_path,
                update=update,
            )

    import_issue_images(journal, user, domain[:-1])
    import_journal_metadata(journal, user, domain[:-1])


def import_journal_metadata(journal, user, url):
    base_url = url

    issn = re.compile(r'E-ISSN: (\d{4}-\d{4})')
    publisher = re.compile(r'Published by (.*)')

    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    logger.info("Extracting journal-level metadata...")

    resp, mime = utils_models.ImportCacheEntry.fetch(url=base_url)

    soup = BeautifulSoup(resp, 'lxml')

    issn_result = soup.find(text=issn)
    issn_match = issn.match(str(issn_result).strip())

    logger.info('ISSN set to: {0}'.format(issn_match.group(1)))
    journal.issn = issn_match.group(1)

    try:
        publisher_result = soup.find(text=publisher)
        publisher_match = str(publisher_result.next_sibling.getText()).strip()
        logger.info('Publisher set to: {0}'.format(publisher_match))
        journal.publisher = publisher_match
        journal.save()
    except Exception as e:
        logger.warning("Error setting publisher: %s" % e)


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
    regex = '\/manager\/userProfile\/(\d+)'

    matches = parse_backend_user_list(url, auth_file, auth_url, regex)

    return matches


def map_review_recommendation(recommentdation):
    recommendations = {
        '2': 'minor_revisions',
        '3': 'major_revisions',
        '5': 'reject',
        '1': 'accept'
    }

    return recommendations.get(recommentdation, None)


def import_issue_images(journal, user, url, import_missing=False, update=False):
    """ Imports all issue images and other issue related content
    Currently also reorders all issues, articles and sections within issues,
    article thumbnails and issue titles.
    :param journal: a journal.models.Journal
    :param user: the owner of the imported content as a core.models.Account
    :param url: the base url of the journal to import from
    :param load_missing: Bool. If true, attempt to import missing articles
    :param update: Bool. If true, update existing article records
    """
    base_url = url

    if not url.endswith('/issue/archive/'):
        url += '/issue/archive/'

    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    resp, mime = utils_models.ImportCacheEntry.fetch(url=url)

    soup = BeautifulSoup(resp, 'lxml')

    from django.conf import settings
    import os
    from django.core.files import File

    for issue in journal.issues():
        issue_num = issue.issue
        pattern = re.compile(r'\/\d+\/volume\/{0}\/issue\/{1}'.format(issue.volume, issue_num))

        img_url_suffix = soup.find(src=pattern)

        if img_url_suffix:
            img_url = base_url + img_url_suffix.get('src')
            logger.info("Fetching {0}".format(img_url))

            resp, mime = utils_models.ImportCacheEntry.fetch(url=img_url)

            path = os.path.join(settings.BASE_DIR, 'files', 'journals', str(journal.id))

            os.makedirs(path, exist_ok=True)

            path = os.path.join(path, 'volume{0}_issue_{0}.graphic'.format(issue.volume, issue_num))

            with open(path, 'wb') as f:
                f.write(resp)

            with open(path, 'rb') as f:
                issue.cover_image.save(path, File(f))

            sequence_pattern = re.compile(r'.*?(\d+)\/volume\/{0}\/issue\/{1}.*'.format(issue.volume, issue_num))

            issue.order = int(sequence_pattern.match(img_url).group(1))

            logger.info("Setting Volume {0}, Issue {1} sequence to: {2}".format(issue.volume, issue_num, issue.order))

            logger.info("Extracting section orders within the issue...")

            new_url = '/{0}/volume/{1}/issue/{2}/'.format(issue.order, issue.volume, issue_num)
            resp, mime = utils_models.ImportCacheEntry.fetch(url=base_url + new_url)

            soup_issue = BeautifulSoup(resp, 'lxml')

            sections_to_order = soup_issue.find_all(name='h2', attrs={'class': 'main-color-text'})
            # Find issue title
            try:
                issue_title = soup_issue.find("div", {"class": "multi-inline"}).find("h1").string
                issue_title = issue_title.strip(" -\n")
                if issue.issue_title and issue_title not in issue.issue_title:
                    issue.issue_title = "{} - {}".format(
                        issue_title, issue.issue_title)
                else:
                    issue.issue_title = issue_title
            except AttributeError as e:
                logger.debug("Couldn't find an issue title: %s" % e)

            #Find issue description
            try:
                desc_parts = soup_issue.find("div", {"class": "article-type-list-block"}).findAll("p", {"class": "p1"})
                issue.issue_description = "\n".join(str(p) for p in desc_parts)
            except AttributeError as e:
                logger.debug("Couldn't extract an issue description %s" % e)


            sections_to_order = soup_issue.find_all(name='h2', attrs={'class': 'main-color-text'})

            # delete existing order models for sections for this issue
            journal_models.SectionOrdering.objects.filter(issue=issue).delete()

            for section_order, section in enumerate(sections_to_order):

                logger.info('[{0}] {1}'.format(section_order, section.getText()))
                order_section, c = models.Section.objects.language('en').get_or_create(
                    name=section.getText().strip(),
                    journal=journal)
                journal_models.SectionOrdering.objects.create(issue=issue,
                                                              section=order_section,
                                                              order=section_order).save()

            import_issue_articles(soup_issue, issue, user, base_url, import_missing, update)

            issue.save()


def import_jms_user(url, journal, auth_file, base_url, user_id):
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    # Fetch the user profile page and parse its metdata
    resp, mime = utils_models.ImportCacheEntry.fetch(url=url, up_auth_file=auth_file, up_base_url=base_url)
    soup_user_profile = BeautifulSoup(resp, 'lxml')
    profile_dict = shared.get_user_profile(soup_user_profile)[0]
    if profile_dict["email"] == "journal@openlibhums.org":
        dummy_email = shared.generate_dummy_email(profile_dict)
        logger.debug("Generated email for author: {}".format(dummy_email))
        profile_dict["email"] = dummy_email

    # add an account for this new user
    account = core_models.Account.objects.filter(email=profile_dict['email'])

    if account is not None and len(account) > 0:
        account = account[0]
        logger.info("Found account for {0}".format(profile_dict['email']))
    else:
        logger.info("Didn't find account for {0}. Creating.".format(profile_dict['email']))

        if profile_dict['Country'] == '—':
            profile_dict['Country'] = None
        else:
            try:
                profile_dict['Country'] = core_models.Country.objects.get(name=profile_dict['Country'])
            except Exception:
                logger.warning(
                    "Country not found: %s" % profile_dict["Country"])
                profile_dict['Country'] = None

        if not profile_dict.get('Salutation') in dict(core_models.SALUTATION_CHOICES):
            profile_dict['Salutation'] = ''

        if profile_dict.get('Middle Name', None) == '—':
            profile_dict['Middle Name'] = ''

        account = core_models.Account.objects.create(email=profile_dict['email'],
                                                     username=profile_dict['Username'],
                                                     institution=profile_dict['Affiliation'],
                                                     first_name=profile_dict['First Name'],
                                                     last_name=profile_dict['Last Name'],
                                                     middle_name=profile_dict.get('Middle Name', None),
                                                     country=profile_dict.get('Country', None),
                                                     biography=profile_dict.get('Bio Statement', None),
                                                     salutation=profile_dict.get('Salutation', None),
                                                     is_active=True)
        account.save()

        if account:
            account.add_account_role(journal=journal, role_slug='author')
            account.add_account_role(journal=journal, role_slug='reviewer')


def process_resp(resp):
    resp = resp.decode("utf-8")

    known_strings = {
        '\\u00a0': " ",
        '\\u00e0': "à",
        '\\u0085': "...",
        '\\u0091': "'",
        '\\u0092': "'",
        '\\u0093': '\\"',
        '\\u0094': '\\"',
        '\\u0096': "-",
        '\\u0097': "-",
        '\\u00F6': 'ö',
        '\\u009a': 'š',
        '\\u00FC': 'ü',
    }

    for string, replacement in known_strings.items():
        resp = resp.replace(string, replacement)
    return resp


def get_input_value_by_name(content, name):
    soup = BeautifulSoup(content, 'lxml')
    value = soup.find('input', {'name': name}).get('value', None)

    return value


def convert_values(value):
    return re.sub(r'[\xc2-\xf4][\x80-\xbf]+', lambda m: m.group(0).encode('latin1').decode('utf-8'), value)


def get_ojs_plugin_response(url, auth_file, up_base_url):
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    # setup auth variables
    do_auth = True
    username = ''
    password = ''
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/39.0.2171.95 Safari/537.36'}

    session = requests.Session()

    # first, check whether there's an auth file
    with open(auth_file, 'r', encoding="utf-8") as auth_in:
        auth_dict = json.loads(auth_in.read())
        do_auth = True
        username = auth_dict['username']
        password = auth_dict['password']

    # load the login page
    auth_url = '{0}{1}'.format(up_base_url, '/login/')
    fetched = session.get(auth_url, headers=headers, stream=True, verify=False)

    csrf_token = get_input_value_by_name(fetched.content, 'csrfmiddlewaretoken')

    post_dict = {'username': username, 'password': password, 'login': 'login', 'csrfmiddlewaretoken': csrf_token}
    fetched = session.post('{0}{1}'.format(up_base_url, '/author/login/'), data=post_dict,
                           headers={'Referer': auth_url,
                                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) '
                                                  'Chrome/39.0.2171.95 Safari/537.36'
                                    })

    fetched = session.get(url, headers=headers, stream=True, verify=False)

    json_out = fetched.json()

    for item in json_out:
        for key, value in item.items():
            if isinstance(value, str):
                item[key] = convert_values(value)
    return json_out


def ojs_plugin_import_review_articles(url, journal, auth_file, base_url):
    resp = get_ojs_plugin_response(url, auth_file, base_url)

    for article_dict in resp:
        create_article_with_review_content(article_dict, journal, auth_file, base_url)
        logger.info('Importing {article}.'.format(article=article_dict.get('title')))


def ojs_plugin_import_editing_articles(url, journal, auth_file, base_url):
    resp = get_ojs_plugin_response(url, auth_file, base_url)

    for article_dict in resp:
        logger.info('Importing {article}.'.format(article=article_dict.get('title')))
        article = create_article_with_review_content(article_dict, journal, auth_file, base_url)
        complete_article_with_production_content(article, article_dict, journal, auth_file, base_url)


def create_article_with_review_content(article_dict, journal, auth_file, base_url):
    date_started = timezone.make_aware(dateparser.parse(article_dict.get('date_submitted')))

    # Create a base article
    article = models.Article(
        journal=journal,
        title=article_dict.get('title'),
        abstract=article_dict.get('abstract'),
        language=article_dict.get('language'),
        stage=models.STAGE_UNDER_REVIEW,
        is_import=True,
        date_submitted=date_started,
    )

    article.save()

    # Check for editors and assign them as section editors.
    editors = article_dict.get('editors', [])

    for editor in editors:
        try:
            account = core_models.Account.objects.get(email=editor)
            account.add_account_role('section-editor', journal)
            review_models.EditorAssignment.objects.create(article=article, editor=account, editor_type='section-editor')
            logger.info('Editor added to article')
        except Exception as e:
            logger.error('Editor account was not found.')
            logger.exception(e)

    # Add a new review round
    round = review_models.ReviewRound.objects.create(article=article, round_number=1)

    # Add keywords
    keywords = article_dict.get('keywords')
    if keywords:
        for i, keyword in enumerate(keywords.split(';')):
            keyword = strip_tags(keyword)
            word, created = models.Keyword.objects.get_or_create(word=keyword)
            models.KeywordArticle.objects.update_or_create(
                keyword=keyword,
                article=article,
                defaults={"order":i},
            )

    # Add authors
    for author in article_dict.get('authors'):
        try:
            author_record = core_models.Account.objects.get(email=author.get('email'))
        except core_models.Account.DoesNotExist:
            author_record = core_models.Account.objects.create(
                email=author.get('email'),
                first_name=author.get('first_name'),
                last_name=author.get('last_name'),
                institution=author.get('affiliation'),
                biography=author.get('bio'),
            )

        # If we have a country, fetch its record
        if author.get('country'):
            try:
                country = core_models.Country.objects.get(code=author.get('country'))
                author_record.country = country
                author_record.save()
            except core_models.Country.DoesNotExist:
                pass
        # Add authors to m2m and create an order record
        article.authors.add(author_record)
        models.ArticleAuthorOrder.objects.create(article=article,
                                                 author=author_record,
                                                 order=article.next_author_sort())

        # Set the primary author
        article.owner = core_models.Account.objects.get(email=article_dict.get('correspondence_author'))
        article.correspondence_author = article.owner

        # Get or create the article's section
        try:
            section = models.Section.objects.language().fallbacks('en').get(journal=journal,
                                                                            name=article_dict.get('section'))
        except models.Section.DoesNotExist:
            section = None

        article.section = section

        article.save()

    # Attempt to get the default review form
    form = setting_handler.get_setting('general',
                                       'default_review_form',
                                       journal,
                                       create=True).processed_value

    if not form:
        try:
            form = review_models.ReviewForm.objects.filter(journal=journal)[0]
        except Exception:
            form = None
            logger.error(
                'You must have at least one review form for the journal before'
                ' importing.'
            )
            exit()

    for review in article_dict.get('reviews'):
        try:
            reviewer = core_models.Account.objects.get(email=review.get('email'))
        except core_models.Account.DoesNotExist:
            reviewer = core_models.Account.objects.create(
                email=review.get('email'),
                first_name=review.get('first_name'),
                last_name=review.get('last_name'),
            )

        # Parse the dates
        date_requested = timezone.make_aware(dateparser.parse(review.get('date_requested')))
        date_due = timezone.make_aware(dateparser.parse(review.get('date_due')))
        date_complete = timezone.make_aware(dateparser.parse(review.get('date_complete'))) if review.get(
            'date_complete') else None
        date_confirmed = timezone.make_aware(dateparser.parse(review.get('date_confirmed'))) if review.get(
            'date_confirmed') else None

        # If the review was declined, setup a date declined date stamp
        review.get('declined')
        if review.get('declined') == '1':
            date_declined = date_confirmed
            date_accepted = None
            date_complete = date_confirmed
        else:
            date_accepted = date_confirmed
            date_declined = None

        new_review = review_models.ReviewAssignment.objects.create(
            article=article,
            reviewer=reviewer,
            review_round=round,
            review_type='traditional',
            visibility='double-blind',
            date_due=date_due,
            date_requested=date_requested,
            date_complete=date_complete,
            date_accepted=date_accepted,
            access_code=uuid.uuid4(),
            form=form
        )

        if review.get('declined') or review.get('recommendation'):
            new_review.is_complete = True

        if review.get('recommendation'):
            new_review.decision = map_review_recommendation(review.get('recommendation'))

        if review.get('review_file_url'):
            filename, mime = shared.fetch_file(base_url, review.get('review_file_url'), None, None, article, None,
                                               handle_images=False, auth_file=auth_file)
            extension = os.path.splitext(filename)[1]

            review_file = shared.add_file(mime, extension, 'Reviewer file', reviewer, filename, article,
                                          galley=False)
            new_review.review_file = review_file

        if review.get('comments'):
            filepath = core_files.create_temp_file(review.get('comments'), 'comment.txt')
            file = open(filepath, 'r', encoding="utf-8")
            comment_file = core_files.save_file_to_article(file,
                                                           article,
                                                           article.owner,
                                                           label='Review Comments',
                                                           save=False)

            new_review.review_file = comment_file

        new_review.save()

    # Get MS File
    ms_file = get_ojs_file(base_url, article_dict.get('manuscript_file_url'), article, auth_file, 'MS File')
    article.manuscript_files.add(ms_file)

    # Get RV File
    rv_file = get_ojs_file(base_url, article_dict.get('review_file_url'), article, auth_file, 'RV File')
    round.review_files.add(rv_file)

    # Get Supp Files
    if article_dict.get('supp_files'):
        for file in article_dict.get('supp_files'):
            file = get_ojs_file(base_url, file.get('url'), article, auth_file, file.get('title'))
            article.data_figure_files.add(file)

    article.save()
    round.save()

    return article


def get_ojs_file(base_url, url, article, auth_file, label):
    filename, mime = shared.fetch_file(base_url, url, None, None, article, None, handle_images=False,
                                       auth_file=auth_file)
    extension = os.path.splitext(filename)[1]
    file = shared.add_file(mime, extension, label, article.owner, filename, article, galley=False)

    return file


def determine_production_stage(article_dict):
    stage = models.STAGE_AUTHOR_COPYEDITING

    publication = True if article_dict.get('publication') and article_dict['publication'].get('date_published') else False
    typesetting = True if article_dict.get('layout') and article_dict['layout'].get('galleys') else False
    proofing = True if typesetting and article_dict.get('proofing') else False

    logger.debug(typesetting, proofing, publication)

    if publication:
        stage = models.STAGE_READY_FOR_PUBLICATION
    elif typesetting and not proofing:
        stage = models.STAGE_TYPESETTING
    elif proofing:
        stage = models.STAGE_PROOFING

    return stage


def attempt_to_make_timezone_aware(datetime):
    if datetime:
        dt = dateparser.parse(datetime)
        return timezone.make_aware(dt)
    else:
        return None


def import_copyeditors(article, article_dict, auth_file, base_url):
    copyediting = article_dict.get('copyediting', None)

    if copyediting:

        initial = copyediting.get('initial')
        author = copyediting.get('author')
        final = copyediting.get('final')

        from copyediting import models

        if initial:
            initial_copyeditor = core_models.Account.objects.get(email=initial.get('email'))
            initial_decision = True if (initial.get('underway') or initial.get('complete')) else False

            logger.info(
                'Adding copyeditor: {copyeditor}'.format(
                    copyeditor=initial_copyeditor.full_name()
                )
            )

            assigned = attempt_to_make_timezone_aware(initial.get('notified'))
            underway = attempt_to_make_timezone_aware(initial.get('underway'))
            complete = attempt_to_make_timezone_aware(initial.get('complete'))

            copyedit_assignment = models.CopyeditAssignment.objects.create(
                article=article,
                copyeditor=initial_copyeditor,
                assigned=assigned,
                notified=True,
                decision=initial_decision,
                date_decided=underway if underway else complete,
                copyeditor_completed=complete,
                copyedit_accepted=complete
            )

            if initial.get('file'):
                file = get_ojs_file(base_url, initial.get('file'), article, auth_file, 'Copyedited File')
                copyedit_assignment.copyeditor_files.add(file)

            if initial and author.get('notified'):
                logger.info('Adding author review.')
                assigned = attempt_to_make_timezone_aware(author.get('notified'))
                complete = attempt_to_make_timezone_aware(author.get('complete'))

                author_review = models.AuthorReview.objects.create(
                    author=article.owner,
                    assignment=copyedit_assignment,
                    assigned=assigned,
                    notified=True,
                    decision='accept',
                    date_decided=complete,
                )

                if author.get('file'):
                    file = get_ojs_file(base_url, author.get('file'), article, auth_file, 'Author Review File')
                    author_review.files_updated.add(file)

            if final and initial_copyeditor and final.get('notified'):
                logger.info('Adding final copyedit assignment.')

                assigned = attempt_to_make_timezone_aware(initial.get('notified'))
                underway = attempt_to_make_timezone_aware(initial.get('underway'))
                complete = attempt_to_make_timezone_aware(initial.get('complete'))

                final_decision = True if underway or complete else False

                final_assignment = models.CopyeditAssignment.objects.create(
                    article=article,
                    copyeditor=initial_copyeditor,
                    assigned=assigned,
                    notified=True,
                    decision=final_decision,
                    date_decided=underway if underway else complete,
                    copyeditor_completed=complete,
                    copyedit_accepted=complete,
                )

                if final.get('file'):
                    file = get_ojs_file(base_url, final.get('file'), article, auth_file, 'Final File')
                    final_assignment.copyeditor_files.add(file)


def import_typesetters(article, article_dict, auth_file, base_url):
    layout = article_dict.get('layout')
    task = None

    if layout.get('email'):
        typesetter = core_models.Account.objects.get(email=layout.get('email'))

        logger.info('Adding typesetter {name}'.format(name=typesetter.full_name()))

        from production import models as production_models

        assignment = production_models.ProductionAssignment.objects.create(
            article=article,
            assigned=timezone.now(),
            notified=True
        )

        assigned = attempt_to_make_timezone_aware(layout.get('notified'))
        accepted = attempt_to_make_timezone_aware(layout.get('underway'))
        complete = attempt_to_make_timezone_aware(layout.get('complete'))

        task = production_models.TypesetTask.objects.create(
            assignment=assignment,
            typesetter=typesetter,
            assigned=assigned,
            accepted=accepted,
            completed=complete,
        )

    galleys = import_galleys(article, layout, auth_file, base_url)

    if task and galleys:
        for galley in galleys:
            task.galleys_loaded.add(galley.file)


def import_proofing(article, article_dict, auth_file, base_url):
    pass


def import_galleys(article, layout_dict, auth_file, base_url):
    galleys = list()

    if layout_dict.get('galleys'):

        for galley in layout_dict.get('galleys'):
            logger.info(
                'Adding Galley with label {label}'.format(
                    label=galley.get('label')
                )
            )
            file = get_ojs_file(base_url, galley.get('file'), article, auth_file, galley.get('label'))

            new_galley = core_models.Galley.objects.create(
                article=article,
                file=file,
                label=galley.get('label'),
            )

            galleys.append(new_galley)

    return galleys


def process_for_copyediting(article, article_dict, auth_file, base_url):
    import_copyeditors(article, article_dict, auth_file, base_url)


def process_for_typesetting(article, article_dict, auth_file, base_url):
    import_copyeditors(article, article_dict, auth_file, base_url)
    import_typesetters(article, article_dict, auth_file, base_url)


def process_for_proofing(article, article_dict, auth_file, base_url):
    import_copyeditors(article, article_dict, auth_file, base_url)
    import_typesetters(article, article_dict, auth_file, base_url)
    import_galleys(article, article_dict, auth_file, base_url)
    import_proofing(article, article_dict, auth_file, base_url)


def process_for_publication(article, article_dict, auth_file, base_url):
    process_for_proofing(article, article_dict, auth_file, base_url)
    # mark proofing complete


def complete_article_with_production_content(article, article_dict, journal, auth_file, base_url):
    """
    Completes the import of journal article that are in editing
    """
    article.stage = determine_production_stage(article_dict)
    article.save()

    logger.debug('Stage: {stage}'.format(stage=article.stage))

    if article.stage == models.STAGE_READY_FOR_PUBLICATION:
        process_for_publication(article, article_dict, auth_file, base_url)
    elif article.stage == models.STAGE_TYPESETTING:
        process_for_typesetting(article, article_dict, auth_file, base_url)
    else:
        process_for_copyediting(article, article_dict, auth_file, base_url)


def import_collections(journal, base_url, owner, update=False):
    collections_url = base_url + '/collections/special'
    resp, mime = utils_models.ImportCacheEntry.fetch(url=collections_url)
    soup = BeautifulSoup(resp, 'html.parser')

    collections_div = soup.find("ul", attrs={"id": "special-collection-grid"})
    if collections_div:
        collections = collections_div.find_all("li")
        for idx, collection_div in enumerate(collections):
            collection_link = collection_div.find(
                "a", attrs={"class": "collection-image"})
            collection_path = shared.get_soup(collection_link, "href")
            coll_url = base_url + collection_path
            collection, created = import_collection(
                journal, coll_url, owner, update)

            collection.order = idx
            if created or update:
                try:
                    desc_div = collection_div.find(
                        "div", attrs={"class": "collections-description"})
                    description = desc_div.find("p").text
                    collection.short_description = description.strip()
                except AttributeError:
                    logger.debug("No description in %s", desc_div)

            collection.save()


def import_collection(journal, url, owner, update=False):
    resp, mime = utils_models.ImportCacheEntry.fetch(url=url)
    soup = BeautifulSoup(resp, 'html.parser')
    base_url = url.split("/collections/special/")[0]

    img_div = soup.find("div", attrs={"class": "collection-image"})
    title = img_div.find("h1").text.strip()
    blurb_div = soup.find("div", attrs={"class": "main-body-block"})
    date_launched = extract_date_launched(blurb_div.find_all("h5"))
    blurb = ''.join(str(tag) for tag in blurb_div.contents)

    coll_type = journal_models.IssueType.objects.get(
        journal=journal, code="collection")
    collection, c = journal_models.Issue.objects.get_or_create(
        issue_type=coll_type,
        journal=journal,
        issue_title=title,
        defaults={"date": date_launched},
    )
    if c:
        logger.info("Created collection: %s", title)

    if c or update:
        import_collection_images(img_div, collection, base_url)
        collection.issue_description = blurb
        collection.date = date_launched
        collection.save()
        articles_div = soup.find("div", attrs={"class": "featured-block"})
        import_issue_articles(
            articles_div, collection, owner, base_url, update, update)

    return collection, c


def import_collection_images(soup, collection, base_url):
    img_path = shared.get_soup(soup.find("img"), "src")
    blob, mime = utils_models.ImportCacheEntry.fetch(url=base_url + img_path)
    image_file = ContentFile(blob)
    image_file.name = "collection-{}-cover.graphic".format(collection.id)
    collection.cover_image = collection.large_image = image_file
    collection.save()


def import_issue_articles(soup, issue, user, base_url, import_missing=False, update=False):
    journal = issue.journal
    logger.info("Extracting article orders within issue...", )
    # delete existing order models for issue
    journal_models.ArticleOrdering.objects.filter(issue=issue).delete()

    pattern = re.compile(r'\/articles\/(.+?)/(.+?)/')
    articles = soup.find_all(href=pattern)

    article_order = 0

    processed = []

    for article_link in articles:
        # parse the URL into a DOI and prefix
        article_url = article_link["href"]
        match = pattern.match(article_url)
        prefix = match.group(1)
        doi = match.group(2)

        # get a proper article object
        article = models.Article.get_article(
            journal, 'doi', '{0}/{1}'.format(prefix, doi))
        if not article and import_missing:
            logger.info(
                "Article %s not found, importing...", article_url)
            article = import_article(journal,user, base_url + article_url)

        if article and article not in processed:
            import_article(journal,user, base_url + article_url, update=update)
            thumb_img = article_link.find("img")
            if thumb_img:
                thumb_path = thumb_img["src"]
                filename, mime = shared.fetch_file(
                    base_url,
                    thumb_path, "",
                    'graphic',
                    article, user,
                )
                shared.add_file(
                    mime, 'graphic', 'Thumbnail',
                    user, filename, article,
                    thumbnail=True,
                )

            # Add article to collection
            if issue.issue_type.code == "collection":
                article.issues.add(issue)

            obj, c = journal_models.ArticleOrdering.objects.get_or_create(
                issue=issue,
                article=article,
                section=article.section,
            )
            obj.order = article_order
            obj.save()


            article_order += 1

        processed.append(article)


def extract_date_launched(headers):
    for header in headers:
        text = header.text
        if text and "Collection launched" in text:
            try:
                raw_date = text.split("Collection launched: ")[-1]
                header.extract()
                return dateparser.parse(raw_date)
            except(IndexError, ValueError):
                logger.debug("Failed to parse collection date: %s", text)
    return None


def split_affiliation(affiliation):
    parts = [p.strip() for p in affiliation.split(',')]
    country = institution = department = None

    if len(parts) == 1:
        institution = parts[0]
    elif len(parts) == 2:
        institution = parts[0]
        country = parts[1]
    else:
        department = parts[0]
        institution = parts[1]
        country = parts[2]
    try:
        country = core_models.Country.objects.get(name=country)
    except core_models.Country.DoesNotExist:
        country = None

    return department, institution, country


def split_name(name):
    parts = name.split(' ')
    return parts[0], parts[1]


def scrape_editorial_team(journal, base_url):
    logger.info("Scraping editorial team page")
    editorial_team_path = '/about/editorialteam/'
    page = requests.get('{}{}'.format(base_url, editorial_team_path))

    soup = BeautifulSoup(page.content, 'lxml')
    main_block = soup.find('div', {'class': 'major-floating-block'})
    divs = main_block.find_all('div', {'class': 'col-md-12'})

    for div in divs:
        # Try to grab the headers
        header = div.find('h2')
        header_sequence = 0
        if header:
            group, c = core_models.EditorialGroup.objects.get_or_create(
                name=header.text.strip(),
                journal=journal,
                sequence=header_sequence
            )
            header_sequence = header_sequence + 1
        else:
            # look for team group
            member_sequence = 0
            member_divs = div.find_all('div', {'class': 'col-md-6'})
            for member_div in member_divs:
                name = member_div.find('h6')
                if name and name.text.strip():
                    affiliation = member_div.find('h5')
                    email_link = member_div.find('a', {'class': 'fa-envelope'})
                    department, institution, country = split_affiliation(affiliation.text)
                    first_name, last_name = split_name(name.text.strip())
                    profile_dict = {
                            'first_name': first_name,
                            'last_name': last_name,
                            'department': department,
                            'institution': institution,
                    }
                    if email_link:
                        email_search = re.search(r'[\w\.-]+@[\w\.-]+', email_link.get('href'))
                        email = email_search.group(0)
                    else:
                        email = generate_dummy_email(profile_dict)
                    profile_dict["username"] = email
                    profile_dict["country"] = country



                    account, c = core_models.Account.objects.update_or_create(
                        email=email,
                        defaults=profile_dict,
                    )
                    bio_div = member_div.find("div", attrs={"class": "well"})
                    if bio_div:
                        bio = bio_div.text.strip()
                        account.biography = bio
                        account.enable_public_profile = True
                        account.save()

                    core_models.EditorialGroupMember.objects.get_or_create(
                        group=group,
                        user=account,
                        sequence=member_sequence
                    )
                    member_sequence = member_sequence + 1


# Checking links and rewrite the ones we know about
# Remove the authorship link

def scrape_policies_page(journal, base_url):
    logger.info("Scraping editorial policies page")
    policy_page_path = '/about/editorialpolicies/'
    page = requests.get('{}{}'.format(base_url, policy_page_path))

    soup = BeautifulSoup(page.content, 'lxml')
    h2 = soup.find('h2', text=' Peer Review Process')

    peer_review_text = ''
    for element in h2.next_siblings:
        if element.name == 'p':
            peer_review_text = peer_review_text + str(element)

    setting_handler.save_setting(
        'general',
        'peer_review_info',
        journal,
        peer_review_text,
    )


def process_header_tags(content, tag):
    headers = content.find_all(tag)

    sections = {}

    for header in headers:
        section_text = ''
        for element in header.next_siblings:
            if element.name == tag:
                break
            else:
                section_text = section_text + str(element)
        sections[header.text.strip()] = section_text

    return sections


def scrape_submissions_page(journal, base_url):
    logger.info("Scraping policies page")
    submission_path = '/about/submissions/'
    page = requests.get('{}{}'.format(base_url, submission_path))
    soup = BeautifulSoup(page.content, 'lxml')
    main_block = soup.find('div', {'class': 'featured-block'})

    sections = process_header_tags(main_block, 'h1')

    if sections.get('Author Guidelines'):
        create_cms_page(
            'author-guidelines',
            'Author Guidelines',
            sections.get('Author Guidelines'),
            journal
        )

    if sections.get('Submission Preparation Checklist'):
        setting_handler.save_setting(
            'general',
            'submission_checklist',
            journal,
            sections.get('Submission Preparation Checklist'),
        )
    if sections.get('Copyright Notice'):
        setting_handler.save_setting(
            'general',
            'copyright_notice',
            journal,
            sections.get('Copyright Notice')
        )
    if sections.get('Publication Fees'):
        setting_handler.save_setting(
            'general',
            'publication_fees',
            journal,
            sections.get('Publication Fees')
        )


def scrape_page(page_url, block_to_find='featured-block'):
    page = requests.get(page_url)
    soup = BeautifulSoup(page.content, 'lxml')
    return str(soup.find('div', {'class': block_to_find}))


def create_cms_page(url, name, content, journal):
    content_type = ContentType.objects.get_for_model(journal)
    defaults = {
        'display_name': name,
        'content': content,
        'is_markdown': False,
    }
    cms_models.Page.objects.get_or_create(
        content_type=content_type,
        object_id=journal.pk,
        name=url,
        defaults=defaults
    )


def scrape_research_integrity_page(journal, base_url):
    logger.info("Scraping research integrity page")
    research_integrity_url = '{}/about/research-integrity/'.format(base_url)
    content = scrape_page(
        research_integrity_url,
    )

    soup = BeautifulSoup(content, 'lxml')
    content = soup
    for div in soup.find_all('div', {'class': 'person-image'}):
        div.decompose()

    soup.select_one('.main-color-text').decompose()
    soup.find('style').decompose()

    for div in soup.find_all('div', {'style': 'border-top: 1px dashed #b3cfd4;'}):
        div.decompose()

    soup.section.unwrap()
    soup.section.unwrap()

    create_cms_page(
        'research-integrity',
        'Research Integrity',
        str(content),
        journal
    )


def scrape_about_page(journal, base_url):
    logger.info("Scraping about page")
    about_url = '{}/about/'.format(base_url)
    content = scrape_page(about_url, block_to_find='main-body-block')
    soup = BeautifulSoup(content, 'lxml')
    sections = process_header_tags(soup, 'h2')

    if sections.get('Focus and Scope'):
        setting_handler.save_setting(
            'general',
            'focus_and_scope',
            journal,
            sections.get('Focus and Scope')
        )
    if sections.get('Publication Frequency'):
        setting_handler.save_setting(
            'general',
            'publication_cycle',
            journal,
            sections.get('Publication Frequency')
        )
    create_cms_page(
        'about',
        'About',
        str(content),
        journal
    )


def generate_dummy_email(profile_dict):
    seed = ''.join(str(val) for val in profile_dict.values())
    hashed = hashlib.md5(str(seed).encode("utf-8")).hexdigest()
    return "{0}@{1}".format(hashed, settings.DUMMY_EMAIL_DOMAIN)
