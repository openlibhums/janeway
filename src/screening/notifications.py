__copyright__ = "Copyright 2026 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

"""
Email notifications for the Screening app, raised via the Janeway events
framework. See events/registration.py for handler wiring and
journal_defaults.json for the templated subject + body strings.
"""

from django.urls import reverse

from core import email as core_email
from utils import notify_helpers, render_template, setting_handler


def _build_email_data(request, subject_setting, body_setting, context):
    """Render the subject and body settings for the active journal and
    return an EmailData ready for send_email."""
    subject = setting_handler.get_setting(
        "email_subject",
        subject_setting,
        request.journal,
    ).processed_value
    body = render_template.get_message_content(request, context, body_setting)
    return core_email.EmailData(subject=subject, body=body)


def send_screener_requested(**kwargs):
    """Handler for ON_SCREENER_REQUESTED.

    Notifies the screener that they have been invited to provide a
    screening report on an article. When the request was raised with
    ``email_data`` (the editor previewed and edited the email body), use
    that verbatim instead of re-rendering from settings. When ``skip``
    is truthy, log the assignment but suppress the email entirely.
    """
    screening_assignment = kwargs["screening_assignment"]
    request = kwargs["request"]
    skip = kwargs.get("skip", False)
    custom_email_data = kwargs.get("email_data")
    article = screening_assignment.article

    description = 'Screening invitation sent for "{0}" to {1}'.format(
        article.title,
        screening_assignment.screener.full_name(),
    )

    if skip:
        notify_helpers.send_slack(request, description, ["slack_editors"])
        return

    if custom_email_data is not None:
        email_data = core_email.EmailData(
            subject=custom_email_data.subject,
            body=custom_email_data.body,
        )
    else:
        screening_requests_url = request.journal.site_url(
            reverse("screening_requests"),
        )
        context = {
            "article": article,
            "screening_assignment": screening_assignment,
            "screening_requests_url": screening_requests_url,
        }
        email_data = _build_email_data(
            request,
            "subject_screening_invitation",
            "screening_invitation",
            context,
        )

    log_dict = {
        "level": "Info",
        "action_text": description,
        "types": "Screening Invitation",
        "target": article,
    }
    core_email.send_email(
        screening_assignment.screener,
        email_data,
        request,
        article=article,
        log_dict=log_dict,
    )
    notify_helpers.send_slack(request, description, ["slack_editors"])


def send_screening_complete(**kwargs):
    """Handler for ON_SCREENING_COMPLETE.

    Notifies the managing editor on the screening assignment that the
    screener has submitted their report.
    """
    screening_assignment = kwargs["screening_assignment"]
    request = kwargs["request"]
    article = screening_assignment.article

    if not screening_assignment.editor:
        return

    screening_article_url = request.journal.site_url(
        reverse("screening_article", kwargs={"article_id": article.pk}),
    )
    context = {
        "article": article,
        "screening_assignment": screening_assignment,
        "screening_article_url": screening_article_url,
    }
    email_data = _build_email_data(
        request,
        "subject_screening_complete",
        "screening_complete",
        context,
    )

    description = (
        '{0} submitted a screening report for "{1}" with recommendation {2}'.format(
            screening_assignment.screener.full_name()
            if screening_assignment.screener
            else "A screener",
            article.title,
            screening_assignment.get_recommendation_display() or "(unrecorded)",
        )
    )
    log_dict = {
        "level": "Info",
        "action_text": description,
        "types": "Screening Report",
        "target": article,
    }
    core_email.send_email(
        screening_assignment.editor,
        email_data,
        request,
        article=article,
        log_dict=log_dict,
    )
    notify_helpers.send_slack(request, description, ["slack_editors"])


def send_screening_passed(**kwargs):
    """Handler for ON_SCREENING_PASSED.

    Notifies the corresponding author that their submission has passed
    screening and is moving into the next workflow stage.
    """
    request = kwargs["request"]
    article = kwargs["article"]
    next_workflow_element = kwargs.get("next_workflow_element")

    if not article.correspondence_author:
        return

    context = {
        "article": article,
        "next_workflow_element": next_workflow_element,
    }
    email_data = _build_email_data(
        request,
        "subject_screening_passed",
        "screening_passed",
        context,
    )

    description = 'Screening-passed notification sent to author of "{0}"'.format(
        article.title,
    )
    log_dict = {
        "level": "Info",
        "action_text": description,
        "types": "Screening Passed",
        "target": article,
    }
    core_email.send_email(
        article.correspondence_author,
        email_data,
        request,
        article=article,
        log_dict=log_dict,
    )
    notify_helpers.send_slack(request, description, ["slack_editors"])


def send_screening_revisions_requested(**kwargs):
    """Handler for ON_SCREENING_REVISIONS_REQUESTED.

    Notifies the corresponding author that an editor has asked them to
    revise their submission. The email contains a link to the revision
    page where the author uploads revised files and a covering letter.
    """
    request = kwargs["request"]
    revision = kwargs["screening_revision"]
    article = revision.article

    if not article.correspondence_author:
        return

    do_revisions_url = request.journal.site_url(
        reverse("do_screening_revisions", kwargs={"revision_id": revision.pk}),
    )
    context = {
        "article": article,
        "screening_revision": revision,
        "do_revisions_url": do_revisions_url,
    }
    email_data = _build_email_data(
        request,
        "subject_screening_revisions_requested",
        "screening_revisions_requested",
        context,
    )

    description = 'Screening revisions requested for "{0}"'.format(article.title)
    log_dict = {
        "level": "Info",
        "action_text": description,
        "types": "Screening Revisions Requested",
        "target": article,
    }
    core_email.send_email(
        article.correspondence_author,
        email_data,
        request,
        article=article,
        log_dict=log_dict,
    )
    notify_helpers.send_slack(request, description, ["slack_editors"])


def send_screening_revisions_completed(**kwargs):
    """Handler for ON_SCREENING_REVISIONS_COMPLETED.

    Notifies the requesting editor that the author has submitted their
    revisions so the editor can reopen a screening round.
    """
    request = kwargs["request"]
    revision = kwargs["screening_revision"]
    article = revision.article

    if not revision.editor:
        return

    article_url = request.journal.site_url(
        reverse("screening_article", kwargs={"article_id": article.pk}),
    )
    context = {
        "article": article,
        "screening_revision": revision,
        "article_url": article_url,
    }
    email_data = _build_email_data(
        request,
        "subject_screening_revisions_completed",
        "screening_revisions_completed",
        context,
    )

    description = 'Screening revisions submitted for "{0}"'.format(article.title)
    log_dict = {
        "level": "Info",
        "action_text": description,
        "types": "Screening Revisions Completed",
        "target": article,
    }
    core_email.send_email(
        revision.editor,
        email_data,
        request,
        article=article,
        log_dict=log_dict,
    )
    notify_helpers.send_slack(request, description, ["slack_editors"])
