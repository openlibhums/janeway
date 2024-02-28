import os
import hashlib
import hmac
from urllib.parse import SplitResult, quote_plus, urlencode
from tqdm import tqdm

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.template.loader import render_to_string

from core.middleware import GlobalRequestMiddleware
from cron.models import Request
from utils import models, notify_helpers
from utils.logger import get_logger
from utils.function_cache import cache
from janeway import __version__ as janeway_version
from journal import models as journal_models
from repository import models as repo_models
from press import models as press_models
from submission import models as submission_models

logger = get_logger(__name__)


def parse_mailgun_webhook(post):
    message_id = post.get('Message-Id')
    token = post.get('token')
    timestamp = post.get('timestamp')
    signature = post.get('signature')
    mailgun_event = post.get('event')

    try:
        event = models.LogEntry.objects.get(message_id=message_id)
    except models.LogEntry.DoesNotExist:
        return 'No log entry with that message ID found.'

    if event and (mailgun_event == 'dropped' or mailgun_event == 'bounced'):
        event.message_status = 'failed'
        event.save()
        send_bounce_notification_to_event_actor(event)
        return 'Message dropped, actor notified.'
    elif event and mailgun_event == 'delivered':
        event.message_status = 'delivered'
        event.save()
        return 'Message marked as delivered.'


def verify_webhook(token, timestamp, signature):
    api_key = settings.MAILGUN_ACCESS_KEY.encode('utf-8')
    timestamp = timestamp.encode('utf-8')
    token = token.encode('utf-8')
    signature = signature.encode('utf-8')

    hmac_digest = hmac.new(key=api_key,
                           msg='{}{}'.format(timestamp, token).encode('utf-8'),
                           digestmod=hashlib.sha256).hexdigest()

    return hmac.compare_digest(signature, hmac_digest.encode('utf-8'))


def send_bounce_notification_to_event_actor(event):
    """
    Attempts to send a notification email to an actor when a message bounces.
    Messages are only send to staff, editors and repository managers.
    """
    actor = event.actor
    target = event.target

    # set to the main contact, and then attempt to find a better match
    press = press_models.Press.objects.all()[0]
    to = press.main_contact

    # fake a request object
    request = Request()
    request.press = press
    request.META = {}
    request.model_content_type = None
    request.user = None

    if actor and target:
        if actor.is_staff or actor.is_superuser:
            to = actor.email

        # target could be an article or a preprint, lets find out
        if isinstance(target, submission_models.Article):
            # check if the actor is an editor for the article's journal
            if actor in target.journal.editors():
                to = actor.email
            request.site_type = target.journal
            request.journal = target.journal
        elif isinstance(target, repo_models.Preprint):
            # check if the actor is a manager for the preprint's repo
            if actor in target.repository.managers.all():
                to = actor.email
            request.site_type = target.repository
            request.repository = target.repository

    # currently this feature is set up for article and preprint emails.
    # if no site type is set, we shouldn't try to send a bounce email.
    if request.site_type:
        # Setup log dict
        log_dict = {
            'level': 'Info',
            'action_text': 'Email Delivery Failed ',
            'types': 'Email Delivery',
            'target': target,
        }

        notify_helpers.send_email_with_body_from_setting_template(
            request=request,
            template='bounced_email_notification',
            subject='subject_bounced_email_notification',
            to=to,
            context={
                'target': target,
                'event': event,
            },
            log_dict=log_dict,
        )


def build_url_for_request(request=None, path="", query=None, fragment=""):
    """ Builds a url from the base url relevant for the current request context
    :request: An instance of django.http.HTTPRequest
    :path: A str indicating the path
    :query: A dictionary with any GET parameters
    :fragment: A string indicating the fragment
    :return: An instance of urllib.parse.SplitResult
    """
    if request is None:
        request = get_current_request()

    return build_url(
        netloc=request.get_host(),
        scheme=request.scheme,
        path=path,
        query=query,
        fragment=fragment,
    )


def replace_netloc_port(netloc, new_port):
    return ":".join((netloc.split(":")[0], new_port))


def build_url(netloc, port=None, scheme=None, path="", query=None, fragment=""):
    """ Builds a url given all its parts
    :netloc: string
    :port: int
    :scheme: string
    :path: string
    :query: A dictionary with any GET parameters
    :fragment: string
    :return: URL string
    """
    if query:
        query = quote_plus(urlencode(query))

    if scheme is None:
        scheme = GlobalRequestMiddleware.get_current_request().scheme

    if port is not None:
        netloc = replace_netloc_port(netloc, port)

    return SplitResult(
        scheme=scheme,
        netloc=netloc,
        path=path,
        query=query or "",
        fragment=fragment,
    ).geturl()


def get_current_request():
    try:
        return GlobalRequestMiddleware.get_current_request()
    except (KeyError, AttributeError):
        return None


def get_janeway_version():
    """ Returns the installed version of janeway
    :return: `string` version
    """
    return str(janeway_version)


def get_log_entries(object):
    content_type = ContentType.objects.get_for_model(object)
    return models.LogEntry.objects.filter(
        content_type=content_type,
        object_id=object.pk,
    )


def generate_sitemap(file, press=None, journal=None, repository=None, issue=None, subject=None):
    """
    Returns a rendered sitemap
    """
    template, context = None, None
    if press:
        journals = journal_models.Journal.objects.filter(
            hide_from_press=False,
            is_remote=False,
        )
        repos = repo_models.Repository.objects.all()
        template = 'common/site_map_index.xml'
        context = {
            'journals': journals,
            'repos': repos,
        }
    elif journal:
        template = 'common/journal_sitemap.xml'
        context = {
            'journal': journal,
        }
    elif repository:
        template = 'common/repo_sitemap.xml',
        context = {
            'repo': repository,
        }
    elif issue:
        template = 'common/issue_sitemap.xml'
        context = {
            'issue': issue,
        }
    elif subject:
        template = 'common/subject_sitemap.xml'
        context = {
            'subject': subject,
        }

    if template and context:
        content = render_to_string(
            template,
            context,
        )
        file.write(content)
    else:
        return 'Must pass a press, journal, issue, repository or subject object.'


def get_sitemap_path(path_parts, file_name):
    path = os.path.join(
        settings.BASE_DIR,
        'files',
        'sitemaps',
        *path_parts,
    )
    if not os.path.exists(path):
        os.makedirs(path)

    file_path = os.path.join(
        path,
        file_name,
    )
    return file_path


def write_journal_sitemap(journal):
    journal_file_path = get_sitemap_path(
        path_parts=[journal.code],
        file_name='sitemap.xml',
    )
    with open(journal_file_path, 'w') as file:
        generate_sitemap(file, journal=journal)
        file.close()


def write_issue_sitemap(issue):
    issue_file_path = get_sitemap_path(
        path_parts=[issue.journal.code],
        file_name='{}_sitemap.xml'.format(issue.pk),
    )
    with open(issue_file_path, 'w') as file:
        generate_sitemap(file, issue=issue)
        file.close()


def write_repository_sitemap(repository):
    repo_file_path = get_sitemap_path(
        path_parts=[repository.code],
        file_name='sitemap.xml',
    )
    with open(repo_file_path, 'w') as file:
        generate_sitemap(file, repository=repository)
        file.close()


def write_subject_sitemap(subject):
    subject_file_path = get_sitemap_path(
        path_parts=[subject.repository.code],
        file_name='{}_sitemap.xml'.format(subject.pk)
    )
    with open(subject_file_path, 'w') as file:
        generate_sitemap(file, subject=subject)
        file.close()


def write_press_sitemap():
    press = press_models.Press.objects.all().first()
    press_sitemap_path = get_sitemap_path(
        path_parts=[],
        file_name='sitemap.xml',
    )
    with open(press_sitemap_path, 'w') as file:
        generate_sitemap(file, press=press)
        file.close()


def get_aware_datetime(unparsed_string, use_noon_if_no_time=True):
    """
    Takes any ISO 8601 compliant date or datetime string
    and returns an aware datetime object.
    If no time information passed,
    noon UTC is assumed.
    """

    import re
    from dateutil import parser as dateparser
    from django.utils.timezone import is_aware, make_aware

    if use_noon_if_no_time and re.fullmatch(
        '[0-9]{4}-[0-9]{2}-[0-9]{2}',
        unparsed_string
    ):
        unparsed_string += ' 12:00'

    parsed_datetime = dateparser.parse(unparsed_string)

    if is_aware(parsed_datetime):
        return parsed_datetime
    else:
        return make_aware(parsed_datetime)

def get_janeway_patch_version():
    from janeway import __version__
    return f"{__version__.major}.{__version__.minor}.{__version__.patch}"
