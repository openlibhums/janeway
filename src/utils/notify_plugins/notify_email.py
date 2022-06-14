import re

from collections import Iterable

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags

from utils import setting_handler
from utils import notify

SANITIZE_FROM_RE = re.compile("\r|\n|\t|\"|<|>|,")


def sanitize_from(from_):
    return re.sub(SANITIZE_FROM_RE, "", from_)


def send_email(subject, to, html, journal, request, bcc=None, cc=None, attachment=None, replyto=None):

    if journal:
        from_email = setting_handler.get_setting('general', 'from_address', journal).value
        html = "{0}<br />{1}".format(html, journal.name)
    elif request.repository:
        # fetches the default setting for this email.
        subject = setting_handler.get_email_subject_setting('email_subject', subject, journal=None)
        from_email = request.press.main_contact
    else:
        from_email = request.press.main_contact

    if isinstance(to, str):
        if settings.DUMMY_EMAIL_DOMAIN in to:
            to = []
        else:
            to = [to]
    elif isinstance(to, Iterable):
        to = [email for email in to if not settings.DUMMY_EMAIL_DOMAIN in email]

    if request and request.user and not request.user.is_anonymous() and request.user.email not in to:
        reply_to = [request.user.email]
        full_from_string = "{0} <{1}>".format(request.user.full_name(), from_email)
    else:
        reply_to = []
        if request:
            full_from_string = "{0} <{1}>".format(
                    sanitize_from(request.site_type.name),
                    from_email
            )
        else:
            full_from_string = from_email

    if replyto:
        reply_to = replyto

    if not reply_to:
        custom_reply_to = setting_handler.get_setting(
            'general', 'replyto_address', journal,
        ).value
        if custom_reply_to:
            reply_to = (custom_reply_to,)


    msg = EmailMultiAlternatives(subject, strip_tags(html), full_from_string, to, bcc=bcc, cc=cc, reply_to=reply_to)
    msg.attach_alternative(html, "text/html")

    if request and request.FILES and request.FILES.getlist('attachment'):
        for file in request.FILES.getlist('attachment'):
            file.open()
            msg.attach(file.name, file.read(), file.content_type)
            file.close()

    return msg.send()


def notify_hook(**kwargs):
    # dummy mock-up of new notification hook defer

    # action is a list of notification targets
    # if the "all" variable is passed, then some types of notification might act, like Slack.
    # Email, though, should only send if it's specifically an email in action, not on "all".
    action = kwargs.pop('action', [])

    if 'email' not in action:
        # email is only sent if list of actions includes "email"
        return

    # pop the args
    subject = kwargs.pop('subject', '')
    to = kwargs.pop('to', '')
    html = kwargs.pop('html', '')
    bcc = kwargs.pop('bcc', [])
    cc = kwargs.pop('cc', [])
    attachment = kwargs.pop('attachment', None)
    request = kwargs.pop('request', None)
    task = kwargs.pop('task', None)

    if request and request.journal:
        subject_setting = setting_handler.get_email_subject_setting('email_subject', subject, request.journal)
        subject = "[{0}] {1}".format(request.journal.code, subject_setting if subject_setting else subject)

    # call the method
    if not task:
        response = send_email(subject, to, html, request.journal, request, bcc, cc, attachment)
    else:
        response = send_email(task.email_subject, task.email_to, task.email_html, task.email_journal, request,
                              task.email_bcc, task.email_cc)

    log_dict = kwargs.get('log_dict', None)

    if not type(to) in [list, tuple, set]:
        to = [to]

    if log_dict:
        notify_contents = {
            'log_dict': log_dict,
            'request': request,
            'response': response,
            'action': ['email_log'],
            'html': html,
            'to': to,
            'email_subject': subject,
        }
        notify.notification(**notify_contents)


def plugin_loaded():
    pass
