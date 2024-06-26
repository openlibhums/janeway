from dataclasses import dataclass, field
from typing import Tuple

from django.conf import ImproperlyConfigured
from django.core.files.uploadedfile import InMemoryUploadedFile

from utils import notify_helpers

@dataclass(frozen=True)
class EmailData:
    subject: str
    body: str = ""
    to: Tuple[str] = field(default_factory=tuple)
    cc: Tuple[str] = field(default_factory=tuple)
    bcc: Tuple[str] = field(default_factory=tuple)
    attachments: Tuple[InMemoryUploadedFile] = field(default_factory=tuple)


def send_email(
    user,
    email_data,
    request,
    article=None,
    preprint=None,
    log_dict=None,
):
    """ A standard way to send email using data from core.forms.EmailForm.

    :param user: The main recipient of the email. Can be None if email_data has recipient
    :type user: Account or NoneType
    :param email_data: The email data, typically generated from EmailForm
    :type email_data: EmailData
    :param request: The request object
    :param article: an article to be used as the log target
    :param preprint: a preprint to be used as the log target
    :param log_dict: log details to be used instead of a generic email log
    """

    if user:
        to = user.email
    elif email_data.to:
        to = email_data.to
    else:
        raise ImproperlyConfigured('Pass a user or email_data with a to field')
    subject = email_data.subject
    message = email_data.body

    if not log_dict:
        target = article or preprint or None
        log_dict = {
            'level': 'Info',
            'action_text': 'Contact User',
            'types': 'Email',
            'target': target
        }

    notify_helpers.send_email_with_body_from_user(
        request,
        subject,
        to,
        message,
        log_dict=log_dict,
        cc=email_data.cc,
        bcc=email_data.bcc,
        attachment=email_data.attachments,
    )
