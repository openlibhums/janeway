import hashlib
import hmac
from urllib.parse import SplitResult, quote_plus, urlencode

from django.conf import settings

from core.middleware import GlobalRequestMiddleware
from cron.models import Request
from utils import models, notify_helpers
from utils.function_cache import cache


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
        attempt_actor_email(event)
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


def attempt_actor_email(event):

    actor = event.actor
    article = event.target

    # Set To to the main contact, and then attempt to find a better match.
    from press import models as pm
    press = pm.Press.objects.all()[0]
    to = press.main_contact

    if actor and article:
        if actor.is_staff or actor.is_superuser:
            # Send an email to this actor
            to = actor.email
            pass
        elif actor and article.journal and actor in article.journal.editors():
            # Send email to this actor
            to = actor.email
        elif actor and not article.journal and actor in press.preprint_editors():
            to = actor.email

    # Fake a request object
    request = Request()
    request.press = press
    request.site_type = press

    body = """
        <p>A message sent to {0} from article {1} (ID: {2}) has been marked as failed.<p>
        <p>Regards,</p>
        <p>Janeway</p>
    """.format(event.to, article.title, article.pk)
    notify_helpers.send_email_with_body_from_user(request,
                                                  'Email Bounced',
                                                  to,
                                                  body,
                                                  log_dict=None)


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

@cache(seconds=None)
def get_janeway_version():
    """ Returns the installed version of janeway
    :return: `string` version
    """
    v = models.Version.objects.filter(rollback=None).order_by("-pk")[0]
    return v.number
