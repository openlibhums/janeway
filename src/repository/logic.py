import hashlib
import json
from dateutil.relativedelta import relativedelta
from user_agents import parse as parse_ua_string
from datetime import datetime, timedelta
from collections import Counter

from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from django.db import IntegrityError, transaction
from django.db.models import (
    CharField,
    Q,
    OuterRef,
    Subquery,
    Value,
    Count,
)
from django.db.models.functions import Concat

from production.logic import save_galley
from core import models as core_models, files
from utils import render_template, shared
from utils.function_cache import cache
from utils.orcid import COMPILED_ORCID_REGEX
from events import logic as event_logic
from repository import models
from submission import models as submission_models
from metrics.logic import get_iso_country_code, iso_to_country_object


def get_month_day_range(date):
    """
    For a date 'date' returns the start and end date for the month of 'date'.
    """
    last_day = date + relativedelta(day=1, months=+1, days=-1)
    first_day = date + relativedelta(day=1)
    return first_day, last_day


def handle_file_upload(request, preprint):
    if "file" in request.FILES:
        label = request.POST.get("label")
        for uploaded_file in request.FILES.getlist("file"):
            save_galley(
                preprint,
                request,
                uploaded_file,
                True,
                label=label,
            )


def determine_action(preprint):
    if preprint.date_accepted and not preprint.date_declined:
        return "accept"
    else:
        return "decline"


def get_pdf(article):
    try:
        try:
            pdf = article.galley_set.get(file__mime_type="application/pdf")
        except core_models.Galley.MultipleObjectsReturned:
            pdf = article.galley_set.filter(file__mime_type="application/pdf")[0]
    except core_models.Galley.DoesNotExist:
        pdf = None

    return pdf


def get_html(article):
    try:
        galley = article.galley_set.get(type="html")
        html = galley.file_content()
    except core_models.Galley.DoesNotExist:
        html = None

    return html


def get_publication_text(request, preprint, action):
    context = {
        "preprint": preprint,
        "request": request,
        "action": action,
    }

    if preprint.date_declined and not preprint.date_published:
        template = request.repository.decline
    else:
        template = request.repository.publication
    email_content = render_template.get_message_content(
        request,
        context,
        template,
        template_is_setting=True,
    )
    return email_content


def raise_comment_event(request, comment):
    kwargs = {
        "request": request,
        "preprint": comment.preprint,
        "comment": comment,
    }
    event_logic.Events.raise_event(
        event_logic.Events.ON_PREPRINT_COMMENT,
        **kwargs,
    )

    messages.add_message(
        request,
        messages.SUCCESS,
        "Your comment has been saved. It has been sent for moderation.",
    )


def comment_manager_post(request, preprint):
    if "comment_public" in request.POST:
        comment_id = request.POST.get("comment_public")
    elif "comment_reviewed" in request.POST:
        comment_id = request.POST.get("comment_reviewed")
    elif "comment_delete" in request.POST:
        comment_id = request.POST.get("comment_delete")
    else:
        return

    comment = get_object_or_404(
        models.Comment,
        pk=comment_id,
        preprint=preprint,
        preprint__repository=request.repository,
    )

    if "comment_public" in request.POST:
        was_public = comment.is_public
        comment.toggle_public()
        if not was_public and comment.is_public:
            event_logic.Events.raise_event(
                event_logic.Events.ON_PREPRINT_COMMENT_PUBLISHED,
                request=request,
                preprint=comment.preprint,
                comment=comment,
            )
    elif "comment_reviewed" in request.POST:
        comment.mark_reviewed()

    if "comment_delete" in request.POST:
        comment.delete()
        messages.add_message(
            request,
            messages.SUCCESS,
            "Comment deleted",
        )


# TODO: Update this implementation
def handle_author_post(request, preprint):
    file = request.FILES.get("file")
    update_type = request.POST.get("upload_type")
    galley_id = request.POST.get("galley_id")
    galley = get_object_or_404(core_models.Galley, article=preprint, pk=galley_id)

    if (
        request.press.preprint_pdf_only
        and not files.check_in_memory_mime(in_memory_file=file) == "application/pdf"
    ):
        messages.add_message(request, messages.WARNING, "You must upload a PDF file.")
        return
    else:
        file = files.save_file_to_article(
            file, preprint, request.user, label=galley.label
        )

    models.VersionQueue.objects.create(
        article=preprint, galley=galley, file=file, update_type=update_type
    )

    messages.add_message(
        request, messages.INFO, "This update has been added to the moderation queue."
    )


# TODO: Update this implementation
def get_pending_update_from_post(request):
    """
    Gets a VersionQueue object from a post value
    :param request: HttpRequest object
    :return: VersionQueue object or None
    """
    update_id = None

    if "approve" in request.POST:
        update_id = request.POST.get("approve")
    elif "decline" in request.POST:
        update_id = request.POST.get("decline")

    if update_id:
        pending_update = get_object_or_404(
            models.VersionQueue,
            pk=update_id,
            date_decision__isnull=True,
            preprint__repository=request.repository,
        )
        return pending_update
    else:
        return None


# TODO: Update this implementation
def approve_pending_update(request):
    """
    Approves a pending versioning request and updates files/galleys.
    :param request: HttpRequest object
    :return: None
    """
    pending_update = get_pending_update_from_post(request)

    if pending_update and not pending_update.approve():
        messages.add_message(
            request,
            messages.WARNING,
            "This update has already been decided.",
        )
    elif pending_update:
        messages.add_message(
            request,
            messages.INFO,
            "New version created.",
        )
        kwargs = {
            "pending_update": pending_update,
            "request": request,
            "action": "accept",
        }
        event_logic.Events.raise_event(
            event_logic.Events.ON_PREPRINT_VERSION_UPDATE,
            **kwargs,
        )
    else:
        messages.add_message(
            request,
            messages.WARNING,
            "No valid pending update found.",
        )

    return redirect(reverse("version_queue"))


def decline_pending_update(request):
    pending_update = get_pending_update_from_post(request)

    if pending_update and not pending_update.decline():
        messages.add_message(
            request,
            messages.WARNING,
            "This update has already been decided.",
        )
    elif pending_update:
        messages.add_message(
            request,
            messages.INFO,
            "New version declined.",
        )
        kwargs = {
            "pending_update": pending_update,
            "request": request,
            "action": "decline",
            "reason": request.POST.get("reason", "No reason supplied."),
        }
        event_logic.Events.raise_event(
            event_logic.Events.ON_PREPRINT_VERSION_UPDATE,
            **kwargs,
        )
    else:
        messages.add_message(
            request,
            messages.WARNING,
            "No valid pending update found.",
        )
    return redirect(reverse("version_queue"))


def handle_delete_version(request, preprint):
    version_id = request.POST.get("delete_version")

    if not version_id:
        messages.add_message(request, messages.WARNING, "No version id supplied")
    else:
        version = get_object_or_404(
            models.PreprintVersion,
            pk=version_id,
            preprint=preprint,
        )
        version.delete()
        messages.add_message(
            request,
            messages.INFO,
            "Version deleted.",
        )


def delete_file(request, preprint):
    """
    Fetches the file to be deleted, checks that it belongs to a preprint
    and deletes it.
    :param request: HttpRequest object
    :param preprint: Preprint object
    :return: None
    """
    file_id = request.POST.get("delete_file")

    if not file_id:
        messages.add_message(request, messages.WARNING, "No File ID supplied.")
    try:
        models.PreprintFile.objects.get(
            pk=file_id,
            preprint=preprint,
        ).delete()
    except models.PreprintFile.DoesNotExist:
        messages.add_message(request, messages.WARNING, "No matching File found.")


def subject_article_pks(user):
    prepint_pks = []
    for subject in user.preprint_subjects():
        for preprint in subject.preprint_set.all():
            prepint_pks.append(preprint.pk)

    return prepint_pks


def get_unpublished_preprints(request, user_subject_pks):
    author_name_subq = (
        submission_models.FrozenAuthor.objects.filter(
            preprint=OuterRef("pk"),
        )
        .annotate(
            full_name=Concat(
                "first_name",
                Value(" "),
                "last_name",
                output_field=CharField(),
            )
        )
        .values("full_name")
    )
    unpublished_preprints = models.Preprint.objects.filter(
        date_published__isnull=True,
        date_submitted__isnull=False,
        date_declined__isnull=True,
        date_accepted__isnull=True,
        repository=request.repository,
    ).annotate(author_full_name=Subquery(author_name_subq[:1]))

    if request.user.is_staff or request.user.is_repository_manager(request.repository):
        return unpublished_preprints
    else:
        return unpublished_preprints.filter(pk__in=user_subject_pks)


def get_published_preprints(request, user_subject_pks):
    author_name_subq = (
        submission_models.FrozenAuthor.objects.filter(
            preprint=OuterRef("pk"),
        )
        .annotate(
            full_name=Concat(
                "first_name",
                Value(" "),
                "last_name",
                output_field=CharField(),
            )
        )
        .values("full_name")
    )
    published_preprints = models.Preprint.objects.filter(
        date_published__isnull=False,
        date_submitted__isnull=False,
        repository=request.repository,
    ).annotate(author_full_name=Subquery(author_name_subq[:1]))

    if request.user.is_staff or request.user.is_repository_manager(request.repository):
        return published_preprints
    else:
        return published_preprints.filter(pk__in=user_subject_pks)


@cache(300)
def list_articles_without_subjects(repository=None):
    preprints = models.Preprint.objects.filter(
        date_submitted__isnull=False,
        subject__isnull=True,
    )
    if repository:
        preprints = preprints.filter(
            repository=repository,
        )
    return preprints


def get_doi(request, preprint):
    """
    Returns either the articles actual DOI or a rendered one using the press' pattern.
    :param request: HttpRequest object
    :param preprint: Preprint object
    :return:
    """
    doi = preprint.get_doi()

    if doi:
        return doi

    else:
        doi = render_template.get_message_content(
            request,
            {"preprint": preprint},
            request.press.get_setting_value("Crossref Pattern"),
            template_is_setting=True,
        )
        return doi


def get_list_of_preprint_journals():
    """
    Returns a list of journals who allow preprints to be submitted to them.
    :return: Queryset of Journal objects
    """
    from journal import models as journal_models

    journals = journal_models.Journal.objects.all()
    journals_accepting_preprints = list()

    for journal in journals:
        setting = journal.get_setting(
            "general",
            "accepts_preprint_submissions",
        )
        if setting:
            journals_accepting_preprints.append(journal)

    return journals_accepting_preprints


def check_duplicates(version_queue):
    preprints = [version_request.preprint for version_request in version_queue]
    return [k for k, v in Counter(preprints).items() if v > 1]


def raise_event(event_type, request, preprint):
    kwargs = {
        "request": request,
        "preprint": preprint,
    }

    if event_type == "accept":
        event_logic.Events.raise_event(
            event_logic.Events.ON_PREPRINT_PUBLICATION,
            **kwargs,
        )


def store_preprint_access(request, preprint, file=None):
    try:
        user_agent = parse_ua_string(request.META.get("HTTP_USER_AGENT", None))
    except TypeError:
        user_agent = None

    if user_agent and not user_agent.is_bot:
        ip = shared.get_ip_address(request)
        iso_country_code = get_iso_country_code(ip)
        country = iso_to_country_object(iso_country_code)
        counter_tracking_id = request.session.get("counter_tracking")
        identifier = counter_tracking_id if counter_tracking_id else hash(ip)

        # Check if someone with this identifier has accessed the same file
        # within the last X seconds
        time_to_check = timezone.now() - timedelta(seconds=30)

        if not models.PreprintAccess.objects.filter(
            preprint=preprint,
            file=file,
            identifier=identifier,
            accessed__gte=time_to_check,
        ).exists():
            models.PreprintAccess.objects.create(
                preprint=preprint,
                file=file,
                identifier=identifier,
                country=country,
            )


def get_review_notification(request, preprint, review):
    url = request.repository.site_url(
        path=reverse(
            "repository_submit_review",
            kwargs={
                "review_id": review.pk,
                "access_code": review.access_code,
            },
        )
    )
    context = {
        "preprint": preprint,
        "request": request,
        "review": review,
        "url": url,
    }
    template = request.repository.review_invitation
    email_content = render_template.get_message_content(
        request,
        context,
        template,
        template_is_setting=True,
    )
    return email_content


def get_submission_type_or_redirect(request):
    """
    Attempts to retrieve submission_type and organisation_unit from request.GET.
    If missing or invalid, returns an HttpResponseRedirect to the start page.
    Otherwise, attaches them to request for later use and returns submission_type.
    """
    submission_type_slug = request.GET.get("submission_type")
    if not submission_type_slug:
        return redirect(reverse("repository_submit"))

    submission_type = models.RepositorySubmissionType.objects.filter(
        repository=request.repository,
        slug=submission_type_slug,
    ).first()

    if not submission_type:
        messages.warning(request, "No submission type found.")
        return redirect(reverse("repository_submit"))

    # Handle OU if present
    ou_code = request.GET.get("ou")
    request.organisation_unit = None

    # Units turned off: ignore the parameter rather than bounce the author.
    if ou_code and request.repository.enable_organisation_units:
        request.organisation_unit = models.RepositoryOrganisationUnit.objects.filter(
            repository=request.repository,
            code=ou_code,
        ).first()

        if not request.organisation_unit:
            messages.warning(request, "Invalid organisational unit.")
            return redirect(reverse("repository_submit"))

    return submission_type


AUTHOR_NAME_FIELDS = (
    "name_prefix",
    "first_name",
    "middle_name",
    "last_name",
    "name_suffix",
)
AUTHOR_DETAIL_FIELDS = AUTHOR_NAME_FIELDS + ("email", "orcid", "affiliation")


def author_details(frozen_author):
    """
    The editable details of a FrozenAuthor, as strings.
    """
    details = {
        field: getattr(frozen_author, field) or "" for field in AUTHOR_NAME_FIELDS
    }
    details["email"] = frozen_author.email or ""
    details["orcid"] = frozen_author.orcid_id or frozen_author.orcid or ""
    details["affiliation"] = frozen_author.institution or ""
    return details


def _normalise_detail(field, value):
    value = " ".join(str(value or "").split())
    if field == "orcid":
        match = COMPILED_ORCID_REGEX.search(value)
        return match.group(0) if match else value
    return value.lower() if field == "email" else value


def changed_author_details(frozen_author, details):
    """
    :param details: dict of proposed details; missing keys are unchanged
    :return: list of detail names whose proposed value differs
    """
    current = author_details(frozen_author) if frozen_author else {}
    return [
        field
        for field in AUTHOR_DETAIL_FIELDS
        if field in details
        and _normalise_detail(field, details[field])
        != _normalise_detail(field, current.get(field))
    ]


def set_author_contact_details(frozen_author, email, orcid, names_changed=False):
    """
    Sets a FrozenAuthor's email address and ORCID without touching any
    linked account.

    A new author, or an author whose email changes to an address that
    belongs to another account, is linked to that account. If the email
    changes along with the name, the record now describes someone else, so
    the old account is unlinked. Values that match the linked account are
    not stored, so the author keeps following the account.
    """
    email = (email or "").strip()
    email_changed = not frozen_author.pk or email.lower() != (
        (frozen_author.email or "").lower()
    )

    if email_changed:
        account = core_models.Account.objects.filter(email__iexact=email).first()
        owner = {
            name: getattr(frozen_author, name)
            for name in ("preprint_id", "version_queue_id", "article_id")
            if getattr(frozen_author, name)
        }
        already_listed = (
            account
            and owner
            and submission_models.FrozenAuthor.objects.filter(author=account, **owner)
            .exclude(pk=frozen_author.pk)
            .exists()
        )
        if account and not already_listed:
            frozen_author.author = account
        elif not frozen_author.pk or names_changed:
            frozen_author.author = None

    if frozen_author.author and email.lower() == frozen_author.author.email.lower():
        frozen_author.frozen_email = ""
    else:
        frozen_author.frozen_email = email

    if orcid is not None:
        orcid = orcid.strip()
        account_orcid = frozen_author.author.orcid if frozen_author.author else ""
        if frozen_author.author and orcid == (account_orcid or ""):
            frozen_author.frozen_orcid = ""
        else:
            frozen_author.frozen_orcid = orcid


def set_author_affiliation(frozen_author, affiliation):
    """
    Sets a FrozenAuthor's affiliation from text. Blank removes it.
    """
    affiliation = (affiliation or "").strip()
    if not affiliation:
        frozen_author.affiliations.delete()
    elif affiliation != frozen_author.institution:
        frozen_author.institution = affiliation


def apply_author_details(frozen_author, details, fields):
    """
    Applies the named details to a saved FrozenAuthor.
    :param details: a dict of details, or a FrozenAuthor to take them from
    :param fields: names from AUTHOR_DETAIL_FIELDS to apply
    """
    if not isinstance(details, dict):
        details = author_details(details)
    names_changed = False
    for field in AUTHOR_NAME_FIELDS:
        if field in fields:
            names_changed = names_changed or field in ("first_name", "last_name")
            setattr(frozen_author, field, details.get(field) or "")
    if "email" in fields or "orcid" in fields:
        set_author_contact_details(
            frozen_author,
            details["email"] if "email" in fields else frozen_author.email,
            details["orcid"] if "orcid" in fields else None,
            names_changed=names_changed,
        )
    frozen_author.save()
    if "affiliation" in fields:
        set_author_affiliation(frozen_author, details.get("affiliation"))


AUTHOR_CHANGE_FIELDS = AUTHOR_NAME_FIELDS + (
    "is_corporate",
    "biography",
    "display_email",
    "email",
    "orcid",
    "affiliations",
    "credit",
)
AUTHOR_CHANGE_LABELS = {
    "name_prefix": _("Name prefix"),
    "first_name": _("First name"),
    "middle_name": _("Middle name"),
    "last_name": _("Last name"),
    "name_suffix": _("Name suffix"),
    "is_corporate": _("Corporate author"),
    "biography": _("Biography"),
    "display_email": _("Display email"),
    "email": _("Email"),
    "orcid": _("ORCID"),
    "affiliations": _("Affiliations"),
    "credit": _("CRediT roles"),
}


def _affiliation_signature(frozen_author):
    return sorted(
        (
            affiliation.organization_id or 0,
            affiliation.title or "",
            affiliation.department or "",
            affiliation.is_primary,
            str(affiliation.start or ""),
            str(affiliation.end or ""),
        )
        for affiliation in frozen_author.affiliations
    )


def _credit_roles(frozen_author):
    return sorted(record.role for record in frozen_author.credits)


def _change_value(frozen_author, field):
    """A comparable value of one of AUTHOR_CHANGE_FIELDS."""
    if field == "affiliations":
        return _affiliation_signature(frozen_author)
    if field == "credit":
        return _credit_roles(frozen_author)
    if field in ("is_corporate", "display_email"):
        return bool(getattr(frozen_author, field))
    if field == "biography":
        return (frozen_author.biography or "").strip()
    if field == "email":
        return (frozen_author.email or "").strip().lower()
    if field == "orcid":
        return frozen_author.orcid_id or (frozen_author.orcid or "").strip()
    return " ".join(str(getattr(frozen_author, field) or "").split())


def display_change_value(frozen_author, field):
    """A readable value of one of AUTHOR_CHANGE_FIELDS, for moderators."""
    if field == "affiliations":
        return "; ".join(str(affiliation) for affiliation in frozen_author.affiliations)
    if field == "credit":
        return "; ".join(str(record) for record in frozen_author.credits)
    if field in ("is_corporate", "display_email"):
        return _("Yes") if getattr(frozen_author, field) else _("No")
    if field == "biography":
        return frozen_author.biography or ""
    if field == "email":
        return frozen_author.email or ""
    if field == "orcid":
        return frozen_author.orcid or ""
    return getattr(frozen_author, field) or ""


def _identity_keys(frozen_author):
    """
    What identifies an author across two author lists, most reliable
    first: their account, their email address, then their name.
    """
    keys = []
    if frozen_author.author_id:
        keys.append(("account", frozen_author.author_id))
    email = (frozen_author.email or "").strip().lower()
    if email:
        keys.append(("email", email))
    name = " ".join(str(frozen_author.full_name() or "").split()).lower()
    if name:
        keys.append(("name", name))
    return keys


class AuthorListChanges:
    """
    How one author list differs from another, for moderators.
    """

    def __init__(self, added, removed, changed, reordered):
        self.added = added
        self.removed = removed
        self.changed = changed
        self.reordered = reordered

    @property
    def has_changes(self):
        return bool(self.added or self.removed or self.changed or self.reordered)


def compare_author_lists(current, proposed):
    """
    Compares two author lists, matching authors by account, then email
    address, then name.
    :param current: the preprint's authors
    :param proposed: an update's authors
    :return: AuthorListChanges, where changed holds (current author,
        proposed author, [(label, current value, proposed value)])
    """
    current = list(current)
    unmatched = list(current)
    pairs = []
    added = []
    for author in proposed:
        match = None
        for key in _identity_keys(author):
            match = next(
                (each for each in unmatched if key in _identity_keys(each)),
                None,
            )
            if match:
                break
        if match:
            unmatched.remove(match)
            pairs.append((match, author))
        else:
            added.append(author)

    changed = []
    for before, after in pairs:
        fields = [
            (
                AUTHOR_CHANGE_LABELS[field],
                display_change_value(before, field),
                display_change_value(after, field),
            )
            for field in AUTHOR_CHANGE_FIELDS
            if _change_value(before, field) != _change_value(after, field)
        ]
        if fields:
            changed.append((before, after, fields))

    kept_in_new_order = [before.pk for before, _after in pairs]
    kept_in_old_order = [author.pk for author in current if author not in unmatched]
    return AuthorListChanges(
        added=added,
        removed=unmatched,
        changed=changed,
        reordered=kept_in_new_order != kept_in_old_order,
    )


def _normalise_answer(text):
    return "\n".join(line.rstrip() for line in str(text or "").strip().splitlines())


def compare_field_answers(current, proposed):
    """
    :return: list of (field name, current answer, proposed answer) for the
        custom fields whose answers differ
    """
    current = {answer.field: answer.answer for answer in current if answer.field}
    proposed = {answer.field: answer.answer for answer in proposed if answer.field}
    return [
        (field.name, current.get(field, ""), proposed.get(field, ""))
        for field in sorted(set(current) | set(proposed), key=lambda f: f.order)
        if _normalise_answer(current.get(field))
        != _normalise_answer(proposed.get(field))
    ]


def _checksum(value):
    return hashlib.sha256(json.dumps(value, default=str).encode()).hexdigest()


def _stored_author_details(frozen_author):
    """
    The details stored on an author record. Values that follow a linked
    account are left out, so account changes do not count as changes.
    """
    return [
        frozen_author.author_id,
        [getattr(frozen_author, field) or "" for field in AUTHOR_NAME_FIELDS],
        frozen_author.is_corporate,
        frozen_author.display_email,
        frozen_author.frozen_email or "",
        frozen_author.frozen_orcid or "",
        frozen_author.frozen_biography or "",
        _affiliation_signature(frozen_author),
        _credit_roles(frozen_author),
    ]


def section_checksums(title, abstract, doi, authors, answers):
    """
    A checksum of each section of metadata an update can change, to tell
    which sections an author changed and which have changed since.
    """
    normalise = models.VersionQueue.normalise_metadata
    return {
        "title": _checksum(normalise(title)),
        "abstract": _checksum(normalise(abstract)),
        "published_doi": _checksum(normalise(doi)),
        "authors": _checksum([_stored_author_details(a) for a in authors]),
        "field_answers": _checksum(
            sorted(
                (answer.field_id or 0, _normalise_answer(answer.answer))
                for answer in answers
            )
        ),
    }


def preprint_checksums(preprint):
    return section_checksums(
        preprint.title,
        preprint.abstract,
        preprint.doi,
        preprint.frozen_authors(),
        preprint.repositoryfieldanswer_set.all(),
    )


def update_checksums(update):
    return section_checksums(
        update.title,
        update.abstract,
        update.published_doi,
        update.authors,
        update.repositoryfieldanswer_set.all(),
    )


class PreprintAuthorList:
    """
    An editable list of preprint authors: a preprint's own author list, or
    the author list of a draft update. Mirrors the journal submission's
    author handling (submission.logic).
    """

    def __init__(self, preprint, version_queue=None):
        self.preprint = preprint
        self.version_queue = version_queue

    @property
    def owner_kwargs(self):
        if self.version_queue:
            return {"version_queue": self.version_queue}
        return {"preprint": self.preprint}

    def authors(self):
        return (
            submission_models.FrozenAuthor.objects.filter(**self.owner_kwargs)
            .select_related("author")
            .order_by("order", "pk")
        )

    def lock(self):
        """
        Locks the list's update or preprint, as approval does, before
        changing the list.
        :return: False if the update is no longer a draft
        """
        if self.version_queue:
            return (
                models.VersionQueue.objects.select_for_update()
                .filter(pk=self.version_queue.pk, is_draft=True)
                .first()
                is not None
            )
        models.Preprint.objects.select_for_update().filter(pk=self.preprint.pk).first()
        return True

    def get(self, author_id):
        if not str(author_id or "").isdigit():
            raise Http404
        return get_object_or_404(self.authors(), pk=author_id)

    def next_order(self):
        last = self.authors().last()
        return last.order + 1 if last else 0

    def _renumber(self):
        for order, author in enumerate(self.authors()):
            if author.order != order:
                author.order = order
                author.save(update_fields=["order"])

    def find_by_email(self, email):
        email = (email or "").strip()
        return (
            self.authors()
            .filter(Q(frozen_email__iexact=email) | Q(author__email__iexact=email))
            .first()
        )

    def add_account(self, account):
        """
        Adds an account, copying its name and affiliations.
        :return: (FrozenAuthor, created)
        """
        existing = self.authors().filter(author=account).first() or (
            self.authors()
            .filter(author__isnull=True, frozen_email__iexact=account.email)
            .first()
        )
        if existing:
            if not existing.author:
                # The same person was added before they had an account.
                existing.author = account
                existing.frozen_email = ""
                existing.save()
            return existing, False

        try:
            with transaction.atomic():
                frozen_author = submission_models.FrozenAuthor.objects.create(
                    author=account,
                    name_prefix=account.salutation or "",
                    first_name=account.first_name or "",
                    middle_name=account.middle_name or "",
                    last_name=account.last_name or "",
                    name_suffix=account.suffix or "",
                    order=self.next_order(),
                    **self.owner_kwargs,
                )
        except IntegrityError:
            # Added by a concurrent request.
            return self.authors().get(author=account), False
        for affiliation in account.affiliations:
            core_models.ControlledAffiliation.objects.create(
                frozen_author=frozen_author,
                title=affiliation.title,
                department=affiliation.department,
                organization=affiliation.organization,
                is_primary=affiliation.is_primary,
                start=affiliation.start,
                end=affiliation.end,
            )
        return frozen_author, True

    def add_from_orcid_record(self, request, cleaned_orcid):
        """
        Adds an author from their public ORCID record, with their first
        ORCID affiliation, as journal submissions do.
        :return: (FrozenAuthor or None, error message or None)
        """
        from core.forms import OrcidAffiliationForm
        from utils import orcid

        orcid_details = orcid.get_orcid_record_details(cleaned_orcid)
        if not orcid_details:
            return None, _(
                "We couldn't retrieve a record from ORCID for %(orcid)s. "
                "Check the ORCID ID and try again later."
            ) % {"orcid": cleaned_orcid}
        emails = orcid_details.get("emails", [])
        for email in emails:
            account = core_models.Account.objects.filter(email__iexact=email).first()
            if account:
                return self.add_account(account)[0], None

        frozen_author = submission_models.FrozenAuthor.objects.create(
            first_name=orcid_details.get("first_name", "") or "",
            last_name=orcid_details.get("last_name", "") or "",
            frozen_email=emails[0] if emails else "",
            frozen_orcid=cleaned_orcid,
            order=self.next_order(),
            **self.owner_kwargs,
        )
        affiliations = orcid_details.get("affiliations", [])
        if affiliations:
            form = OrcidAffiliationForm(
                orcid_affiliation=affiliations[0],
                data={"frozen_author": frozen_author},
            )
            if form.is_valid():
                form.save()
        return frozen_author, None

    def add_from_search(self, request, search_term):
        """
        Adds an author found by email address or ORCID: an existing
        account, or a public ORCID record.
        """
        from utils.forms import clean_orcid_id

        search_term = (search_term or "").strip()
        author, created, error = None, False, None
        existing = self.find_by_email(search_term)
        account = core_models.Account.objects.filter(email__iexact=search_term).first()
        if existing:
            author = existing
        elif account:
            author, created = self.add_account(account)
        else:
            try:
                cleaned_orcid = clean_orcid_id(search_term)
            except ValueError:
                cleaned_orcid = None
            if cleaned_orcid:
                account = core_models.Account.objects.filter(
                    orcid__icontains=cleaned_orcid,
                ).first()
                existing = self.authors().filter(frozen_orcid=cleaned_orcid).first()
                if existing:
                    author = existing
                elif account:
                    author, created = self.add_account(account)
                else:
                    author, error = self.add_from_orcid_record(request, cleaned_orcid)
                    created = bool(author)

        if author and created:
            messages.add_message(
                request,
                messages.SUCCESS,
                _("%(author_name)s is now an author.")
                % {"author_name": author.full_name()},
            )
        elif author:
            messages.add_message(
                request,
                messages.INFO,
                _("%(author_name)s is already an author.")
                % {"author_name": author.full_name()},
            )
        elif error:
            messages.add_message(request, messages.ERROR, error)
        else:
            messages.add_message(
                request,
                messages.WARNING,
                _('No author found with search term: "%(search_term)s".')
                % {"search_term": search_term},
            )
        return author

    def add_from_form(self, request):
        """
        Adds an author from the journal's new author form. Accounts are
        linked by email but never created.
        :return: (FrozenAuthor or None, bound form)
        """
        from submission.forms import EditFrozenAuthor

        form = EditFrozenAuthor(request.POST)
        email = request.POST.get("frozen_email", "")
        existing = self.find_by_email(email) if email else None
        if existing:
            messages.add_message(
                request,
                messages.INFO,
                _("%(author_name)s is already an author.")
                % {"author_name": existing.full_name()},
            )
            return existing, form
        if not form.is_valid():
            messages.add_message(
                request,
                messages.WARNING,
                _("Could not add the author manually."),
            )
            return None, form

        account = (
            core_models.Account.objects.filter(email__iexact=email).first()
            if email
            else None
        )
        if account:
            frozen_author, _created = self.add_account(account)
        else:
            frozen_author = form.save(commit=False)
            for name, value in self.owner_kwargs.items():
                setattr(frozen_author, name, value)
            frozen_author.order = self.next_order()
            frozen_author.save()
        messages.add_message(
            request,
            messages.SUCCESS,
            _("%(author_name)s added.") % {"author_name": frozen_author.full_name()},
        )
        return frozen_author, form

    def remove(self, author):
        author.delete()
        self._renumber()

    def reorder(self, author, change_order):
        """
        Moves an author "top", "up", "down" or "bottom", as journal
        submissions do.
        """
        authors = list(self.authors())
        old = authors.index(author)
        new = {
            "top": 0,
            "up": max(old - 1, 0),
            "down": min(old + 1, len(authors) - 1),
            "bottom": len(authors) - 1,
        }[change_order]
        authors.insert(new, authors.pop(old))
        for order, each in enumerate(authors):
            if each.order != order:
                each.order = order
                each.save(update_fields=["order"])
        return new != old

    def restore(self, author):
        """
        Puts an author from the preprint's own list back on a draft
        update's list, as they are on the preprint.
        """
        return author.copy(
            preprint=None,
            version_queue=self.version_queue,
            order=self.next_order(),
        )

    def replace(self, rows, editor=None):
        """
        Replaces the list with a complete new one, as the API takes it.
        Authors already listed are matched by email address, then by name,
        and keep their account link, affiliations and CRediT roles; details
        left out are unchanged. Accounts are linked by email but never
        created or changed.

        :param rows: list of dicts of AUTHOR_DETAIL_FIELDS
        :param editor: the user making the change; authors they cannot
            edit (e.g. co-authors with accounts) keep their details
        """
        existing = list(self.authors())
        matched = []
        for data in rows:
            details = dict(data)
            if "institution" in details:
                details["affiliation"] = details.pop("institution")
            frozen_author = self._take_match(existing, details)
            matched.append((frozen_author, details))
        # Remove the authors who are not listed first, so their accounts
        # can be linked to the new rows.
        for frozen_author in existing:
            frozen_author.delete()

        for order, (frozen_author, details) in enumerate(matched):
            if frozen_author is None:
                frozen_author = submission_models.FrozenAuthor(**self.owner_kwargs)
                for field in AUTHOR_NAME_FIELDS:
                    setattr(frozen_author, field, details.get(field) or "")
                frozen_author.order = order
                set_author_contact_details(
                    frozen_author,
                    details.get("email") or "",
                    details.get("orcid") or "",
                )
                frozen_author.save()
                if details.get("affiliation"):
                    set_author_affiliation(frozen_author, details["affiliation"])
                elif frozen_author.author:
                    # As a new author added through the web form would.
                    frozen_author.author.snapshot_affiliations(frozen_author)
            else:
                fields = [
                    field
                    for field in changed_author_details(frozen_author, details)
                    if field != "affiliation" or details.get("affiliation")
                ]
                if editor and not frozen_author.can_edit(editor):
                    fields = []
                frozen_author.order = order
                apply_author_details(frozen_author, details, fields)

    @staticmethod
    def _row_key(email, first_name, last_name):
        email = (email or "").strip().lower()
        if email:
            return ("email", email)
        return (
            "name",
            " ".join(f"{first_name or ''} {last_name or ''}".split()).lower(),
        )

    def _take_match(self, existing, details):
        """
        Takes the listed author a row describes: the one with its email
        address, or, failing that, one without an account with its name.
        """
        email = (details.get("email") or "").strip().lower()
        name = self._row_key("", details.get("first_name"), details.get("last_name"))
        candidates = [
            frozen_author
            for frozen_author in existing
            if email and (frozen_author.email or "").lower() == email
        ] or [
            frozen_author
            for frozen_author in existing
            if name[1]
            and not frozen_author.author_id
            and self._row_key("", frozen_author.first_name, frozen_author.last_name)
            == name
        ]
        if candidates:
            existing.remove(candidates[0])
            return candidates[0]
        return None

    def differs_from(self, rows):
        """
        Whether a complete author list, as replace() takes it, differs from
        this one.
        """
        current = list(self.authors())
        keys = [
            self._row_key(row.get("email"), row.get("first_name"), row.get("last_name"))
            for row in rows
        ]
        if keys != [
            self._row_key(author.email, author.first_name, author.last_name)
            for author in current
        ]:
            return True
        return any(
            changed_author_details(
                author,
                {
                    key: value
                    for key, value in row.items()
                    if key != "affiliation" or value
                },
            )
            for author, row in zip(current, rows)
        )


def open_update(preprint):
    """
    The preprint's update that is still open: the author's draft, or an
    update awaiting moderation.
    """
    return (
        models.VersionQueue.objects.filter(
            preprint=preprint, date_decision__isnull=True
        )
        .order_by("-is_draft", "-pk")
        .first()
    )


def start_update(preprint, update_type, resume=True):
    """
    Starts a draft update holding a complete copy of the preprint's title,
    abstract, DOI, authors and custom field answers, or returns the
    author's existing draft. A preprint has one open update at a time, so
    each update starts from the metadata the previous one left.
    :param resume: False to refuse, rather than return, an existing draft
    :return: (VersionQueue or None, error message or None)
    """
    with transaction.atomic():
        preprint = models.Preprint.objects.select_for_update().get(pk=preprint.pk)
        update = open_update(preprint)
        if update and not update.is_draft:
            return None, _(
                "There is already an update awaiting moderation. You can "
                "start another once a moderator has decided on it."
            )
        if update and not resume:
            return None, _(
                "This preprint has a draft update on the website. Submit or "
                "discard it there first."
            )
        if update:
            set_update_type(update, update_type)
            return update, None

        update = models.VersionQueue.objects.create(
            preprint=preprint,
            update_type=update_type,
            is_draft=True,
            title=preprint.title,
            abstract=preprint.abstract,
            published_doi=preprint.doi,
            started_from=preprint_checksums(preprint),
        )
        for frozen_author in preprint.frozen_authors():
            frozen_author.copy(preprint=None, version_queue=update)
        for answer in preprint.repositoryfieldanswer_set.all():
            answer.copy(preprint=None, version_queue=update)
        return update, None


def set_update_type(update, update_type):
    """
    Changes a draft's type. Metadata corrections have no file, so one
    uploaded for another type is discarded.
    """
    if update.update_type == update_type:
        return
    update.update_type = update_type
    replaced = update.file if update_type == "metadata_correction" else None
    if replaced:
        update.file = None
    update.save()
    if replaced:
        delete_unused_draft_file(replaced)


def set_update_field_answers(update, answers):
    """
    Sets a draft update's custom field answers.
    :param answers: dict of RepositoryField to answer text; blank or None
        clears the field. Fields not included keep their answer.
    """
    for field, text in answers.items():
        update.repositoryfieldanswer_set.filter(field=field).delete()
        if text not in (None, ""):
            models.RepositoryFieldAnswer.objects.create(
                field=field,
                version_queue=update,
                answer=str(text).strip(),
            )


def duplicate_accounts(authors):
    """The accounts listed more than once on an author list."""
    accounts = [author.author for author in authors if author.author_id]
    return {account for account in accounts if accounts.count(account) > 1}


def submit_update(update):
    """
    Puts a draft update in the moderation queue, recording the sections the
    author changed. Only those are applied on approval, so changes made to
    the others in the meantime are kept.
    :return: an error message if it cannot be submitted, otherwise None
    """
    with transaction.atomic():
        update = models.VersionQueue.objects.select_for_update().get(pk=update.pk)
        if not update.is_draft:
            return _("This update has already been submitted.")
        authors = list(update.authors)
        if not authors:
            return _("You must list at least one author.")
        duplicates = duplicate_accounts(authors)
        if duplicates:
            return _("%(names)s is listed more than once.") % {
                "names": ", ".join(account.full_name() for account in duplicates)
            }
        if update.update_type != "metadata_correction" and not update.file:
            return _("You must upload a file.")

        checksums = update_checksums(update)
        update.changed_sections = [
            section
            for section in models.VersionQueue.UPDATE_SECTIONS
            if checksums.get(section, update.started_from.get(section))
            != update.started_from.get(section)
            or (section == "file" and update.file)
        ]
        update.is_draft = False
        update.date_submitted = timezone.now()
        update.save()
    return None


def discard_update(update):
    """
    :return: False if the update is no longer a draft
    """
    with transaction.atomic():
        update = (
            models.VersionQueue.objects.select_for_update()
            .filter(pk=update.pk, is_draft=True)
            .first()
        )
        if update is None:
            return False
        file = update.file
        update.delete()
        if file:
            delete_unused_draft_file(file)
    return True


def lock_author(authors, author_id):
    """
    Gets an author for editing, with the update or preprint that owns it
    locked as approval locks them, so an edit cannot interleave with an
    approval or write back an author that approval has moved.
    :param authors: the authors the user may reach
    """
    author = get_object_or_404(authors, pk=author_id)
    while True:
        if author.version_queue_id:
            models.VersionQueue.objects.select_for_update().filter(
                pk=author.version_queue_id,
            ).first()
        else:
            models.Preprint.objects.select_for_update().filter(
                pk=author.related_preprint.pk,
            ).first()
        locked = get_object_or_404(authors, pk=author_id)
        if (locked.version_queue_id, locked.preprint_id) == (
            author.version_queue_id,
            author.preprint_id,
        ):
            return locked
        author = locked


def delete_unused_draft_file(preprint_file):
    """
    Deletes a file a draft update no longer uses, unless a version, another
    update or the preprint itself still points at it.
    """
    in_use = (
        models.PreprintVersion.objects.filter(file=preprint_file).exists()
        or models.VersionQueue.objects.filter(file=preprint_file).exists()
        or models.Preprint.objects.filter(submission_file=preprint_file).exists()
    )
    if not in_use:
        preprint_file.delete()


def resolve_account_merge(from_account, to_account):
    """
    Before merging from_account into to_account, removes from_account's
    entries on preprint author lists (live, update and snapshot) that
    already list to_account, so the merge does not list the same person
    twice.
    """
    for owner in ("preprint", "version_queue", "preprint_version"):
        listed = submission_models.FrozenAuthor.objects.filter(
            author=to_account,
            **{f"{owner}__isnull": False},
        ).values(owner)
        submission_models.FrozenAuthor.objects.filter(
            author=from_account,
            **{f"{owner}__in": listed},
        ).delete()


def upload_must_be_pdf(request):
    return bool(request.repository.limit_upload_to_pdf)


def is_pdf_upload(request):
    return (
        files.check_in_memory_mime(in_memory_file=request.FILES.get("file"))
        == "application/pdf"
    )
