__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from bs4 import BeautifulSoup
import csv
from dateutil import parser as dateparser
import os
from os import listdir, makedirs
from os.path import isfile, join
import requests
from shutil import copyfile
from urllib.parse import urlencode
from uuid import uuid4

from django.contrib import messages
from django.conf import settings
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.template.loader import get_template
from django.core.validators import validate_email, ValidationError
from django.utils.timezone import make_aware

from core import models as core_models, files
from journal import models as journal_models, issue_forms
from journal.forms import SearchForm
from submission import models as submission_models
from identifiers import models as identifier_models
from utils import render_template, notify_helpers
from utils.logger import get_logger
from utils.logic import get_current_request
from utils.notify_plugins import notify_email
from events import logic as event_logic

logger = get_logger(__name__)


def install_cover(journal, request):
    """ Installs the default cover for the journal (stored in Files/journal/<id>/cover.png)

    :param journal: the journal object
    :param request: the current request or None
    :return: None
    """
    owner = request.user if request.user is not None else core_models.Account(id=1)

    thumbnail_file = core_models.File(
        mime_type="image/png",
        original_filename="cover.png",
        uuid_filename="cover.png",
        label="Journal logo",
        description="Logo for the journal",
        owner=owner
    )

    thumbnail_file.save()

    journal.thumbnail_image = thumbnail_file
    journal.save()


def list_scss(journal):
    """ Lists the SCSS override files for a journal

    :param journal: the journal in question
    :return: a list of SCSS files
    """
    scss_path = join(
            settings.BASE_DIR, 'files', 'styling', 'journals', str(journal.id))
    try:
        makedirs(scss_path, exist_ok=True)
        file_paths = [
                join(scss_path, f)
                for f in listdir(scss_path) if isfile(join(scss_path, f))
        ]
    except FileNotFoundError:
        logger.warning("Failed to load scss from %s" % scss_path)
        file_paths = []

    return file_paths


def create_galley_from_file(file_object, article_object, owner=None):
    # we copy the file here so that the user submitting has no control over the typeset files
    # N.B. os.path.splitext[1] always returns the final file extension, even in a multi-dotted (.txt.html etc.) input
    new_filename = str(uuid4()) + str(os.path.splitext(file_object.uuid_filename)[1])
    folder_structure = os.path.join(settings.BASE_DIR, 'files', 'articles', str(article_object.id))

    old_path = os.path.join(folder_structure, str(file_object.uuid_filename))
    new_path = os.path.join(folder_structure, str(new_filename))

    copyfile(old_path, new_path)

    # clone the file model object to a new galley
    new_file = core_models.File(
        mime_type=file_object.mime_type,
        original_filename=file_object.original_filename,
        uuid_filename=new_filename,
        label=file_object.label,
        description=file_object.description,
        owner=owner,
        is_galley=True
    )

    new_file.save()

    core_models.Galley.objects.create(
        article=article_object,
        file=new_file,
        label=new_file.label,
    )


def get_best_galley(article, galleys):
    """
    Attempts to get the best galley possible for an article
    :param article: Article object
    :param galleys: list of Galley objects
    :return: Galley object
    """
    if article.render_galley and article.render_galley.public:
        return article.render_galley

    try:
        try:
            html_galley = galleys.get(
                file__mime_type__in=files.HTML_MIMETYPES,
                public=True,
            )
            return html_galley
        except core_models.Galley.DoesNotExist:
            pass

        try:
            xml_galley = galleys.get(
                file__mime_type__in=files.XML_MIMETYPES,
                public=True,
            )
            return xml_galley
        except core_models.Galley.DoesNotExist:
            pass
    except core_models.Galley.MultipleObjectsReturned:
        pass

    return None


def get_galley_content(article, galleys, recover=False):
    """
    Gets the best galley and returns its content
    :param article: Article object
    :param galleys: list of Galley objects
    :return: Inline content of the galley, HTML, or a blank string
    """
    galley = get_best_galley(article, galleys)
    if galley:
        return galley.file_content(recover=recover)
    else:
        return ''


def get_doi_data(article):
    request = get_current_request()
    try:
        doi = identifier_models.Identifier.objects.get(id_type='doi', article=article)
        doi_url= doi.get_doi_url()
        logger.info("Fetching %s.." % doi_url)
        r = requests.get(doi_url, timeout=settings.HTTP_TIMEOUT_SECONDS)
        return [r, doi]
    except requests.exceptions.Timeout:
        if request:
            messages.add_message(
                request,
                messages.WARNING,
                "Timed out reaching %s" % doi_url,
            )
        return [None, doi]
    except Exception as e:
        logger.error("Error getting DOI data: %s", e)
        return [None, None]


def handle_new_issue(request):
    form = issue_forms.NewIssue(request.POST, journal=request.journal)

    if form.is_valid():
        new_issue = form.save(commit=False)
        new_issue.journal = request.journal
        new_issue.save()
    else:
        new_issue = None
    return [form, 'issue', new_issue]


def handle_assign_issue(request, article, issues):
    try:
        issue_to_assign = journal_models.Issue.objects.get(pk=request.POST.get('assign_issue', None))

        if issue_to_assign in issues:
            issue_to_assign.articles.add(article)
            issue_to_assign.save()
            messages.add_message(request, messages.SUCCESS, 'Article assigned to issue.')
        else:

            messages.add_message(request, messages.WARNING, 'Issue not in this journals issue list.')
    except journal_models.Issue.DoesNotExist:
        messages.add_message(request, messages.WARNING, 'Issue does no exist.')


def handle_unassign_issue(request, article, issues):
    try:
        issue_to_unassign = journal_models.Issue.objects.get(pk=request.POST.get('unassign_issue', None))

        if issue_to_unassign in issues:
            issue_to_unassign.articles.remove(article)
            issue_to_unassign.save()
            messages.add_message(request, messages.SUCCESS, 'Article unassigned from Issue.')
        else:

            messages.add_message(request, messages.WARNING, 'Issue not in this journals issue list.')
    except journal_models.Issue.DoesNotExist:
        messages.add_message(request, messages.WARNING, 'Issue does no exist.')


def handle_set_pubdate(request, article):
    date = request.POST.get('date')
    time = request.POST.get('time')

    date_time_str = "{0} {1}".format(date, time)

    try:
        date_time = dateparser.parse(date_time_str)
        article.date_published = make_aware(date_time)
        article.fixedpubcheckitems.set_pub_date = True
        article.fixedpubcheckitems.save()
        article.save()

        messages.add_message(
            request, messages.SUCCESS,
            'Publication Date set to {0}'.format(article.date_published)
        )

        return [date_time, []]
    except ValueError:
        return [date_time_str, ['Not a recognised Date/Time format. Date: 2016-12-16, Time: 20:20.']]


def get_notify_author_text(request, article):
    context = {
        'article': article,
    }

    return render_template.get_message_content(request, context, 'author_publication')


def notify_author(request, article):
    kwargs = {
        'request': request,
        'article': article,
        'user_message': request.POST.get('notify_author_email', 'No message from Editor.'),
        'section_editors': request.POST.get('section_editors', False),
        'peer_reviewers': request.POST.get('peer_reviewers', False),
    }

    event_logic.Events.raise_event(event_logic.Events.ON_AUTHOR_PUBLICATION,
                                   task_object=article,
                                   **kwargs)

    article.fixedpubcheckitems.notify_the_author = True
    article.fixedpubcheckitems.save()
    messages.add_message(request, messages.INFO, 'Author notified.')


def set_render_galley(request, article):
    galley_id = request.POST.get('render_galley')

    if galley_id:
        galley = core_models.Galley.objects.get(pk=galley_id)
        article.render_galley = galley
        article.fixedpubcheckitems.select_render_galley = True
        article.fixedpubcheckitems.save()
        article.save()

        messages.add_message(request, messages.SUCCESS, 'Render galley has been set.')
    else:
        messages.add_message(request, messages.WARNING, 'No galley id supplied.')


def set_article_image(request, article):
    from core import logic as core_logic

    if 'delete_image' in request.POST:
        delete_id = request.POST.get('delete_image')
        file_to_delete = get_object_or_404(core_models.File, pk=delete_id, article_id=article.pk)

        if file_to_delete == article.large_image_file and request.user.is_staff or request.user == file_to_delete.owner:
            file_to_delete.delete()

        article.fixedpubcheckitems.select_article_image = False
        article.fixedpubcheckitems.save()

    if request.POST and request.FILES:
        uploaded_file = request.FILES.get('image_file')

        if not article.large_image_file:
            new_file = files.save_file_to_article(uploaded_file, article, request.user)
            new_file.label = 'Banner image'
            new_file.description = 'Banner image'
            new_file.privacy = 'public'
            new_file.save()

            article.large_image_file = new_file
            article.save()
            messages.add_message(request, messages.SUCCESS, 'New file loaded')
        else:
            new_file = files.overwrite_file(
                    uploaded_file,
                    article.large_image_file,
                    ('articles', article.pk),
            )
            article.large_image_file = new_file
            article.save()
            messages.add_message(request, messages.SUCCESS, 'File overwritten.')

            article.fixedpubcheckitems.select_article_image = True
            article.fixedpubcheckitems.save()

        core_logic.resize_and_crop(new_file.self_article_path(), [750, 324], 'middle')


def send_contact_message(new_contact, request):
    body = new_contact.body.replace('\n', '<br>')
    message = """
    <p>This message is from {0}'s contact form.</p>
    <br />
    <p>From: {1}</p>
    <p>To: {2}</p>
    <p>Subject: {3}</p>
    <p>Body:</p>
    <p>{4}</p>
    """.format(request.journal if request.journal else request.press, new_contact.sender, new_contact.recipient,
               new_contact.subject, body)

    notify_email.send_email(
        new_contact.subject,
        new_contact.recipient,
        message,
        request.journal,
        request,
        replyto=[new_contact.sender],
    )


def handle_article_controls(request, sections):
    if request.POST:
        page = request.GET.get('page', 1)
        filters = request.POST.getlist('filter[]')
        show = int(request.POST.get('show', 10))
        sort = request.POST.get('sort', '-date_published')
        filters = [int(filter) for filter in filters]

        return page, show, filters, sort, set_article_session_variables(request, page, filters, show, sort), True
    else:
        page = request.GET.get('page', 1)
        filters = request.session.get('article_filters', [section.pk for section in sections])
        show = request.session.get('article_show', 10)
        sort = request.session.get('article_sort', '-date_published')
        active_filters = request.session.get('active_filters', False)

        return page, show, filters, sort, None, active_filters


def set_article_session_variables(request, page, filters, show, sort):
    request.session['article_filters'] = filters
    request.session['article_show'] = show
    request.session['article_sort'] = sort
    request.session['active_filters'] = True

    return redirect("{0}?page={1}".format(reverse('journal_articles'), page))


def unset_article_session_variables(request):
    del request.session['article_filters']
    del request.session['article_show']
    del request.session['article_sort']
    del request.session['active_filters']

    request.session.modified = True

    page = request.GET.get('page', 1)

    return redirect("{0}?page={1}".format(reverse('journal_articles'), page))


def handle_search_controls(request, search_term=None, keyword=None, redir=False, sort='title'):
    """Takes in request and handles post and get and handles for search
    :param request: required Request object
    :param search_term: None or incoming st
    :param keyword: None or incoming keyword
    :param redir: False or will be processed in set_search_GET_vars
    :param sort: 'title' or incoming sort
    :return: strings: search_term, keyword, sort, and redirect() or None.
    """
    if request.POST:

        form = SearchForm(request.POST)
        if form.is_valid():
            search_term = form.cleaned_data['article_search']
            sort = form.cleaned_data['sort']

            if search_term:
                form = SearchForm({'article_search':search_term, 'sort':sort})
            else:
                # must get keyword from the GET request. there is no way to POST a keyword in current implementation.
                keyword = request.GET.get('keyword', False)
                form = SearchForm({'article_search':'', 'sort':sort})
            return search_term, keyword, sort, form, set_search_GET_variables(search_term, keyword, sort)
        # if form not valid no redir to send form w/errors
        else:
            return search_term, keyword, sort, form, redir
    else:
        search_term = request.GET.get('article_search', '')
        keyword = request.GET.get('keyword', False)
        sort = request.GET.get('sort', 'title')
        if keyword:
            form = SearchForm({'article_search':'', 'sort': sort})
        else:
            form = SearchForm({'article_search':search_term, 'sort': sort})

        return search_term, keyword, sort, form, None


def set_search_GET_variables(search_term=False, keyword=False, sort='title'):
    """Sets the incoming variables to be GET params and returns redirect
    :param search_term: string or false
    :param keyword: string or false
    :param sort: incoming string or 'title'
    :return: redirect()
    """
    if search_term:
        get_params = urlencode({'article_search' : search_term, 'sort' : sort})
        redir_str = '{0}?{1}'.format(reverse('search'), get_params)
    elif keyword:
        get_params = urlencode({'keyword' : keyword, 'sort' : sort})
        redir_str = '{0}?{1}'.format(reverse('search'), get_params)
    else:
        redir_str = reverse('search')

    return redirect(redir_str)


def fire_submission_notifications(**kwargs):
    request = kwargs.get('request')

    active_notifications = journal_models.Notifications.objects.filter(journal=request.journal,
                                                                       active=True,
                                                                       type='submission')
    handle_notification(active_notifications, 'submission', **kwargs)


def fire_acceptance_notifications(**kwargs):
    request = kwargs.get('request')
    active_notifications = journal_models.Notifications.objects.filter(journal=request.journal,
                                                                       active=True,
                                                                       type='acceptance')
    handle_notification(active_notifications, 'acceptance', **kwargs)


def handle_notification(notifications, type, **kwargs):
    request = kwargs.pop('request')
    article = kwargs.pop('article')
    domain = article.correspondence_author.email.split('@')[1]

    for notification in notifications:
        if notification.domain == domain:
            notify_helpers.send_email_with_body_from_setting_template(request,
                                                                      'notification_{0}'.format(type),
                                                                      'Article Notification',
                                                                      notification.user.email,
                                                                      {'article': article,
                                                                       'notification': notification})


def create_html_snippet(note):
    template = get_template('elements/notes/note_snippet.html')
    html_content = template.render({'note': note})

    return html_content


def validate_to_list(to_list):
    """Removes any strings from a list that aren't an email address"""
    for address in to_list:
        try:
            validate_email(address)
        except ValidationError:
            to_list.remove(address)

    return to_list


def resend_email(article, log_entry, request, form):
    to_list = [x.strip() for x in form.cleaned_data['to'].split(';') if x]
    valid_email_addresses = validate_to_list(to_list)

    subject = form.cleaned_data['subject']
    message = form.cleaned_data['body']
    log_dict = {'level': 'Info',
                'action_text': 'Resending an email.',
                'types': 'Email Resend',
                'target': article}

    notify_helpers.send_email_with_body_from_user(request, subject, valid_email_addresses, message, log_dict=log_dict)


def send_email(user, form, request, article):
    subject = form.cleaned_data['subject']
    message = form.cleaned_data['body']

    log_dict = {
        'level': 'Info',
        'action_type': 'Contact User',
        'types': 'Email',
        'target': article if article else user
    }

    notify_helpers.send_email_with_body_from_user(
        request,
        subject,
        user.email,
        message,
        log_dict=log_dict,
        cc=form.cleaned_data['cc'],
    )


def get_table_from_html(table_name, content):
    """
    Uses BS4 to fetch an HTML table.
    :param table_name: ID of the tabe eg T1
    :param content: HTML Content that contains the table
    :return: A table object
    """

    soup = BeautifulSoup(str(content), 'lxml')
    table_div = soup.find("div", {'id': table_name})
    table = table_div.find("table")
    return table


def parse_html_table_to_csv(table, table_name):
    filepath = files.get_temp_file_path_from_name('{0}.csv'.format(table_name))
    headers = [th.text for th in table.select("tr th")]

    with open(filepath, "w", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(headers)
        wr.writerows([[td.text for td in row.find_all("td")] for row in table.select("tr + tr")])

    return filepath


def potential_issue_editors(journal, current_editors):
    return {role.user for role in
            core_models.AccountRole.objects.filter(
                journal=journal,
                user__is_active=True,
            ).select_related('user').exclude(
                user__in=current_editors,
            )}


def sort_issues(request, issue_list):
    """
    Sorts issues by date either asc or dsc
    :param request: HttpRequest
    :param issue_list: Issue queryset for sorting
    :return: None
    """
    sort_type = request.POST.get('sort', None)

    if not sort_type:
        messages.add_message(
            request,
            messages.WARNING,
            'No sort type provided.',
        )

        return

    if sort_type == 'date_sort_desc':
        order = '-date'
    else:
        order = 'date'

    ordered_issues = issue_list.order_by(order)

    for order, issue in enumerate(ordered_issues):
        issue.order = order
        issue.save()


def merge_issues(destination, to_merge):
    """ Moves the articles from to_merge issues into the destination issue
    :param destination: models.Issue
    :param destination: list(models.Issue):
    """
    for issue in to_merge:
        assert destination.journal == issue.journal, "Issues don't belong to "
        "the same journal"
        for article in list(issue.articles.all()):
            destination.articles.add(article)
            if article.primary_issue != issue:
                article.primary_issue = destination
            article.save()
        issue.delete()


def merge_sections(destination, to_merge):
    """ Moves the articles from to_merge sections into the destination section
    :param destination: submission.models.Section
    :param destination: list(submission.models.Section):
    """
    for section in to_merge:
        assert destination.journal == section.journal, "Sections don't belong "
        "to the same journal"
        for article in list(section.article_set.all()):
            article.section = destination
            article.save()
        section.delete()
