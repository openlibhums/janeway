from dataclasses import dataclass, field
from typing import Tuple

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
        user, email_data, request, article=None, preprint=None,
        log_dict=None,
    ):
    subject = email_data.subject
    message = email_data.body

    if not log_dict:
        target = article or preprint or None
        log_dict = {
            'level': 'Info',
            'action_type': 'Contact User',
            'types': 'Email',
            'target': target
        }

    notify_helpers.send_email_with_body_from_user(
        request,
        subject,
        user.email,
        message,
        log_dict=log_dict,
        cc=email_data.cc,
        bcc=email_data.bcc,
        attachment=email_data.attachments,
    )
