"""
Request a copy: a reader asks for a copy of a locked author's accepted
manuscript, the author chosen for the record agrees or declines, and an
approved reader gets a download link that works for a week.

The author's address is never shown to the reader. The author's answer,
with when and by whom it was given, is kept as the record of permission.
"""

import codecs
import json
import os
from functools import lru_cache

from django.conf import settings
from django.template import Context, Template
from django.urls import reverse
from django.utils import timezone

from repository import models
from utils import models as utils_models, notify_helpers


def absolute(repository, path):
    return repository.site_url(path=path)


def decide_url(copy_request):
    return absolute(
        copy_request.preprint.repository,
        reverse("repository_copy_request_decide", kwargs={"token": copy_request.token}),
    )


def download_url(copy_request):
    return absolute(
        copy_request.preprint.repository,
        reverse(
            "repository_copy_request_download",
            kwargs={"token": copy_request.download_token},
        ),
    )


@lru_cache(maxsize=1)
def default_emails():
    path = os.path.join(settings.BASE_DIR, "utils/install/repository_settings.json")
    with codecs.open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)[0]


def send(request, copy_request, setting, to, subject):
    """Email ``to`` with the repository's ``setting`` email (its default if
    the repository hasn't one)."""
    repository = copy_request.preprint.repository
    text = getattr(repository, setting, None) or default_emails()[setting]
    body = Template(text).render(
        Context(
            {
                "copy_request": copy_request,
                "preprint": copy_request.preprint,
                "repository": repository,
                "request": request,
                "decide_url": decide_url(copy_request),
                "download_url": (
                    download_url(copy_request) if copy_request.download_token else ""
                ),
            }
        )
    )
    notify_helpers.send_email_with_body_from_user(
        request,
        subject,
        to,
        body,
        log_dict={
            "level": "Info",
            "action_text": "Request a copy: {}".format(subject),
            "types": "Request a copy",
            "target": copy_request.preprint,
        },
    )


def log(request, copy_request, description, actor=None):
    utils_models.LogEntry.add_entry(
        "Request a copy",
        description,
        "Info",
        actor,
        request,
        copy_request.preprint,
    )


def create(request, preprint_file, form):
    """Store a reader's request and email the author chosen for the record."""
    preprint = preprint_file.preprint
    copy_request = form.save(commit=False)
    copy_request.preprint = preprint
    copy_request.file = preprint_file
    copy_request.asked_name, copy_request.asked_email = (
        preprint.copy_request_recipient()
    )
    copy_request.save()
    log(
        request,
        copy_request,
        "{} ({}) asked for a copy of {}; {} was asked.".format(
            copy_request.name,
            copy_request.email,
            preprint_file.original_filename,
            copy_request.asked_email or "nobody (no author email)",
        ),
    )
    if copy_request.asked_email:
        send(
            request,
            copy_request,
            "copy_request_to_author",
            copy_request.asked_email,
            "A request for a copy of {}".format(preprint.title),
        )
    return copy_request


def decide(request, copy_request, approve, by=None):
    """Record the answer and tell the reader. ``by`` is the manager who
    answered, or None when it's the author, through their link."""
    if approve:
        copy_request.approve(by=by)
        setting = "copy_request_approved"
        subject = "Your copy of {}".format(copy_request.preprint.title)
    else:
        copy_request.decline(by=by)
        setting = "copy_request_declined"
        subject = "Your request for a copy of {}".format(copy_request.preprint.title)
    who = by.full_name() if by else "the author ({})".format(copy_request.asked_email)
    log(
        request,
        copy_request,
        "Copy request from {} {} by {}.".format(
            copy_request.email,
            "approved" if approve else "declined",
            who,
        ),
        actor=by,
    )
    send(request, copy_request, setting, copy_request.email, subject)


def expire(request, now=None):
    """Mark requests with no answer in time as expired and tell the readers.
    Returns how many expired."""
    now = now or timezone.now()
    cutoff = now - timezone.timedelta(days=models.CopyRequest.ANSWER_DAYS)
    stale = models.CopyRequest.objects.filter(
        status=models.CopyRequest.STATUS_PENDING, created__lte=cutoff
    ).select_related("preprint__repository")
    count = 0
    for copy_request in stale:
        copy_request.status = models.CopyRequest.STATUS_EXPIRED
        copy_request.save(update_fields=["status"])
        # A stand-in request from cron: the email's sender comes from these.
        request.repository = copy_request.preprint.repository
        request.site_type = copy_request.preprint.repository
        request.press = copy_request.preprint.repository.press
        log(
            request,
            copy_request,
            "Copy request from {} expired.".format(copy_request.email),
        )
        send(
            request,
            copy_request,
            "copy_request_expired",
            copy_request.email,
            "Your request for a copy of {}".format(copy_request.preprint.title),
        )
        count += 1
    return count
