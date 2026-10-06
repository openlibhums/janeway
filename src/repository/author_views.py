"""
Preprint author editing. Mirrors the journal submission author pages and
affiliation views (submission.views) so that preprint authors use the same
FrozenAuthor records, forms and ROR-backed ControlledAffiliations.

An author list is either a preprint's live list (during submission, or for
moderators) or the proposed list of the author's draft update.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext_lazy as _

from core import models as core_models
from core.forms import ConfirmDeleteForm, OrcidAffiliationForm, OrganizationNameForm
from core.logic import create_organization_name, reverse_with_next
from core.views import GenericFacetedListView
from events import logic as event_logic
from repository import forms, logic as repository_logic, models
from security.decorators import (
    is_repository_manager,
    preprint_editor_or_author_required,
    submission_authorised,
)
from submission import forms as submission_forms, models as submission_models
from utils import orcid
from utils.forms import clean_orcid_id


def handle_author_list_post(request, author_list):
    """
    Handles the author list actions shared by every author list page:
    add self, search, add by form, remove and reorder.
    :return: (handled, new author form)
    """
    new_author_form = submission_forms.EditFrozenAuthor()
    post = request.POST
    if "add_self" in post:
        author, created = author_list.add_account(request.user)
        messages.add_message(
            request,
            messages.SUCCESS if created else messages.INFO,
            (
                _("%(author_name)s is now an author.")
                if created
                else _("%(author_name)s is already an author.")
            )
            % {"author_name": author.full_name()},
        )
    elif "search_authors" in post:
        author_list.add_from_search(request, post.get("author_search_text"))
    elif "add_author" in post:
        author, new_author_form = author_list.add_from_form(request)
        if author:
            new_author_form = submission_forms.EditFrozenAuthor()
        else:
            return False, new_author_form
    elif "remove_author" in post:
        author = author_list.get(post.get("remove_author"))
        author_list.remove(author)
        messages.add_message(
            request,
            messages.SUCCESS,
            _("%(author_name)s removed.") % {"author_name": author.full_name()},
        )
    elif "restore_author" in post and author_list.version_queue:
        removed = {
            author.pk: author for author in author_list_changes(author_list).removed
        }
        restore_pk = post.get("restore_author", "")
        author = removed.get(int(restore_pk)) if restore_pk.isdigit() else None
        if author is None:
            raise Http404
        author_list.restore(author)
        messages.add_message(
            request,
            messages.SUCCESS,
            _("%(author_name)s restored.") % {"author_name": author.full_name()},
        )
    elif post.get("change_order") in ("top", "up", "down", "bottom"):
        author = author_list.get(post.get("author_pk"))
        author_list.reorder(author, post.get("change_order"))
    else:
        return False, new_author_form
    return True, new_author_form


def author_list_changes(author_list):
    """
    For a draft update, how its author list differs from the preprint's.
    """
    if not author_list.version_queue:
        return None
    return repository_logic.compare_author_lists(
        author_list.preprint.frozen_authors(),
        author_list.authors(),
    )


def author_list_context(request, author_list, new_author_form, back_url):
    authors = [
        (author, author.can_edit(request.user))
        for author in author_list.authors().prefetch_related(
            "controlledaffiliation_set"
        )
    ]
    return {
        "preprint": author_list.preprint,
        "version_queue": author_list.version_queue,
        "authors": authors,
        "authors_without_affiliations": [
            (author, can_edit)
            for author, can_edit in authors
            if not author.controlledaffiliation_set.all()
        ],
        "author_changes": author_list_changes(author_list),
        "new_author_form": new_author_form,
        "user_is_author": author_list.authors().filter(author=request.user).exists(),
        "author_list_url": back_url,
    }


@submission_authorised
@transaction.atomic
def repository_authors(request, preprint_id):
    """
    The author step of a new submission.
    """
    preprint = get_object_or_404(
        models.Preprint,
        pk=preprint_id,
        repository=request.repository,
        owner=request.user,
        date_submitted__isnull=True,
    )
    author_list = repository_logic.PreprintAuthorList(preprint)
    new_author_form = submission_forms.EditFrozenAuthor()
    this_url = reverse("repository_authors", kwargs={"preprint_id": preprint.pk})

    if request.method == "POST":
        author_list.lock()
        if "complete" in request.POST:
            if author_list.authors().exists():
                return redirect(
                    reverse("repository_files", kwargs={"preprint_id": preprint.pk})
                )
            messages.add_message(
                request,
                messages.WARNING,
                _("You must add at least one author."),
            )
            return redirect(this_url)
        handled, new_author_form = handle_author_list_post(request, author_list)
        if handled:
            return redirect(this_url)

    context = author_list_context(request, author_list, new_author_form, this_url)
    return render(request, "admin/repository/submit/authors.html", context)


@is_repository_manager
@transaction.atomic
def repository_manager_authors(request, preprint_id):
    """
    Moderators edit a preprint's live author list.
    """
    preprint = get_object_or_404(
        models.Preprint,
        pk=preprint_id,
        repository=request.repository,
    )
    author_list = repository_logic.PreprintAuthorList(preprint)
    new_author_form = submission_forms.EditFrozenAuthor()
    this_url = reverse(
        "repository_manager_authors",
        kwargs={"preprint_id": preprint.pk},
    )
    if request.method == "POST":
        author_list.lock()
        handled, new_author_form = handle_author_list_post(request, author_list)
        if handled:
            return redirect(this_url)

    context = author_list_context(request, author_list, new_author_form, this_url)
    return render(request, "admin/repository/manager_authors.html", context)


def get_draft_update(request, preprint_id, update_id):
    preprint = get_object_or_404(
        models.Preprint,
        pk=preprint_id,
        stage__in=models.SUBMITTED_STAGES,
        repository=request.repository,
    )
    drafts = models.VersionQueue.objects.filter(preprint=preprint, is_draft=True)
    if request.method == "POST":
        # Locked, so a change cannot reopen or alter a submitted update.
        drafts = drafts.select_for_update()
    draft = get_object_or_404(drafts, pk=update_id)
    if not (
        preprint.owner == request.user
        or request.user.is_staff
        or request.user.is_repository_manager(request.repository)
    ):
        raise Http404
    return preprint, draft


@require_POST
@login_required
def repository_submit_update(request, preprint_id, action):
    """
    Starts (or resumes) the owner's draft update and opens it.
    """
    preprint = get_object_or_404(
        models.Preprint,
        pk=preprint_id,
        stage__in=models.SUBMITTED_STAGES,
        repository=request.repository,
        owner=request.user,
    )
    draft, error = repository_logic.start_update(preprint, action)
    if error:
        messages.add_message(request, messages.WARNING, error)
        return redirect(
            reverse("repository_author_article", kwargs={"preprint_id": preprint.pk})
        )
    return redirect(
        reverse(
            "repository_update_draft",
            kwargs={"preprint_id": preprint.pk, "update_id": draft.pk},
        )
    )


@preprint_editor_or_author_required
@transaction.atomic
def repository_update_draft(request, preprint_id, update_id):
    """
    A draft update: the author prepares the new metadata, file, custom
    field answers and author list, then submits it for moderation.
    """
    preprint, draft = get_draft_update(request, preprint_id, update_id)
    author_list = repository_logic.PreprintAuthorList(preprint, draft)
    this_url = reverse(
        "repository_update_draft",
        kwargs={"preprint_id": preprint.pk, "update_id": draft.pk},
    )
    article_url = reverse(
        "repository_author_article",
        kwargs={"preprint_id": preprint.pk},
    )
    takes_file = draft.update_type != "metadata_correction"

    version_form = forms.VersionForm(instance=draft, preprint=preprint)
    file_form = forms.FileForm(preprint=preprint) if takes_file else None
    field_form = forms.UpdateFieldAnswersForm(
        preprint=preprint,
        version_queue=draft,
        prefix="fields",
    )
    new_author_form = submission_forms.EditFrozenAuthor()

    if request.method == "POST":
        if "discard_draft" in request.POST:
            repository_logic.discard_update(draft)
            messages.add_message(request, messages.INFO, _("Draft update discarded."))
            return redirect(article_url)

        if "upload_file" in request.POST and takes_file:
            file_form = forms.FileForm(
                request.POST,
                request.FILES,
                preprint=preprint,
            )
            if (
                request.FILES.get("file")
                and repository_logic.upload_must_be_pdf(request)
                and not repository_logic.is_pdf_upload(request)
            ):
                file_form.add_error(
                    None, _("You must upload a PDF for your manuscript")
                )
            if file_form.is_valid():
                replaced = draft.file
                draft.file = file_form.save()
                draft.save()
                if replaced:
                    repository_logic.delete_unused_draft_file(replaced)
                messages.add_message(request, messages.SUCCESS, _("File uploaded."))
                return redirect(this_url)
        elif "save_draft" in request.POST or "submit_update" in request.POST:
            version_form = forms.VersionForm(
                request.POST,
                instance=draft,
                preprint=preprint,
            )
            field_form = forms.UpdateFieldAnswersForm(
                request.POST,
                preprint=preprint,
                version_queue=draft,
                prefix="fields",
            )
            if version_form.is_valid() and field_form.is_valid():
                draft = version_form.save()
                field_form.save()
                if "save_draft" in request.POST:
                    messages.add_message(request, messages.SUCCESS, _("Draft saved."))
                    return redirect(this_url)
                error = repository_logic.submit_update(draft)
                if error:
                    messages.add_message(request, messages.WARNING, error)
                    return redirect(this_url)
                transaction.on_commit(
                    lambda: event_logic.Events.raise_event(
                        event_logic.Events.ON_PREPRINT_NEW_VERSION,
                        request=request,
                        new_version=draft,
                        preprint=preprint,
                    )
                )
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    _("Your update has been submitted for moderation."),
                )
                return redirect(article_url)
        else:
            handled, new_author_form = handle_author_list_post(request, author_list)
            if handled:
                return redirect(this_url)

    context = author_list_context(request, author_list, new_author_form, this_url)
    context.update(
        {
            "draft": draft,
            "action": draft.update_type,
            "version_form": version_form,
            "file_form": file_form,
            "field_form": field_form,
        }
    )
    return render(request, "admin/repository/update_draft.html", context)


# Author details and affiliations, as in submission.views.


def get_preprint_author(request, preprint_id, author_id):
    """
    An author on a preprint's live list or on its draft update that the
    user can edit.
    """
    preprint = get_object_or_404(
        models.Preprint,
        pk=preprint_id,
        repository=request.repository,
    )
    authors = submission_models.FrozenAuthor.objects.filter(
        Q(preprint=preprint)
        | Q(version_queue__preprint=preprint, version_queue__is_draft=True)
    )
    if request.method == "POST":
        author = repository_logic.lock_author(authors, author_id)
    else:
        author = get_object_or_404(authors, pk=author_id)
    if not author.can_edit(request.user):
        raise Http404
    return preprint, author


def default_author_list_url(request, preprint, author):
    if author.version_queue_id:
        return reverse(
            "repository_update_draft",
            kwargs={"preprint_id": preprint.pk, "update_id": author.version_queue_id},
        )
    if preprint.date_submitted is None and preprint.owner == request.user:
        return reverse("repository_authors", kwargs={"preprint_id": preprint.pk})
    return reverse("repository_manager_authors", kwargs={"preprint_id": preprint.pk})


def safe_next_url(request):
    """
    The "next" URL, if it is a path on this site.
    """
    next_url = request.GET.get("next", "")
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return ""


def done(request, preprint, author):
    return redirect(
        safe_next_url(request) or default_author_list_url(request, preprint, author)
    )


def author_page_context(request, preprint, author, **extra):
    context = {
        "preprint": preprint,
        "author": author,
        "author_list_url": safe_next_url(request)
        or default_author_list_url(request, preprint, author),
    }
    context.update(extra)
    return context


@login_required
@transaction.atomic
def repository_edit_author(request, preprint_id, author_id):
    """
    Edit an author's name, biography and identifiers, and their
    affiliations. Linked accounts are never changed.
    """
    preprint, author = get_preprint_author(request, preprint_id, author_id)
    next_url = safe_next_url(request)
    form = None

    if request.method == "GET" and "edit_author" in request.GET:
        form = submission_forms.EditFrozenAuthor(instance=author)
    elif request.method == "POST" and "save_author" in request.POST:
        form = submission_forms.EditFrozenAuthor(request.POST, instance=author)
        if form.is_valid():
            form.save()
            messages.add_message(
                request,
                messages.SUCCESS,
                _("Name, bio, and identifiers saved."),
            )
            return redirect(
                reverse_with_next(
                    "repository_edit_author",
                    next_url,
                    kwargs={"preprint_id": preprint.pk, "author_id": author.pk},
                )
            )

    context = author_page_context(request, preprint, author, form=form)
    return render(request, "admin/repository/edit_author.html", context)


@method_decorator(login_required, name="dispatch")
class RepositoryOrganizationListView(GenericFacetedListView):
    """
    Search ROR organizations to add as an affiliation of a preprint author.
    """

    model = core_models.Organization
    template_name = "admin/core/organization_search.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        preprint, author = get_preprint_author(
            self.request,
            int(self.kwargs.get("preprint_id")),
            int(self.kwargs.get("author_id")),
        )
        context["preprint"] = preprint
        context["author"] = author
        return context

    def get_queryset(self, *args, **kwargs):
        queryset = super().get_queryset(*args, **kwargs)
        # Exclude user-created organizations from search results
        return queryset.exclude(custom_label__isnull=False)

    def get_facets(self):
        return {"q": {"type": "search", "field_label": "Search"}}


@login_required
@transaction.atomic
def repository_organization_name_create(request, preprint_id, author_id):
    preprint, author = get_preprint_author(request, preprint_id, author_id)
    next_url = safe_next_url(request)
    form = OrganizationNameForm()
    if request.method == "POST":
        org_name = create_organization_name(request)
        if org_name:
            return redirect(
                reverse_with_next(
                    "repository_affiliation_create",
                    next_url,
                    kwargs={
                        "preprint_id": preprint.pk,
                        "author_id": author.pk,
                        "organization_id": org_name.custom_label_for.pk,
                    },
                )
            )
    context = author_page_context(request, preprint, author, form=form)
    return render(request, "admin/core/organizationname_form.html", context)


@login_required
@transaction.atomic
def repository_organization_name_update(
    request, preprint_id, author_id, organization_name_id
):
    preprint, author = get_preprint_author(request, preprint_id, author_id)
    organization_name = get_object_or_404(
        core_models.OrganizationName,
        pk=organization_name_id,
        custom_label_for__controlledaffiliation__frozen_author=author,
    )
    affiliation = core_models.ControlledAffiliation.objects.filter(
        organization__custom_label=organization_name,
        frozen_author=author,
    ).first()
    if affiliation is None:
        raise Http404
    form = OrganizationNameForm(instance=organization_name)
    if request.method == "POST":
        form = OrganizationNameForm(request.POST, instance=organization_name)
        if form.is_valid():
            shared = (
                core_models.ControlledAffiliation.objects.filter(
                    organization=affiliation.organization,
                )
                .exclude(pk=affiliation.pk)
                .exists()
            )
            if shared:
                # Other records (another version, a draft, someone's profile)
                # use this organization, so rename only this affiliation's.
                affiliation.organization = core_models.Organization.objects.create()
                affiliation.save()
                organization = core_models.OrganizationName.objects.create(
                    value=form.cleaned_data["value"],
                    custom_label_for=affiliation.organization,
                )
            else:
                organization = form.save()
            messages.add_message(
                request,
                messages.SUCCESS,
                _("Custom organization updated: %(organization)s")
                % {"organization": organization},
            )
            return done(request, preprint, author)
    context = author_page_context(
        request, preprint, author, form=form, affiliation=affiliation
    )
    return render(request, "admin/core/organizationname_form.html", context)


@login_required
@transaction.atomic
def repository_affiliation_create(request, preprint_id, author_id, organization_id):
    preprint, author = get_preprint_author(request, preprint_id, author_id)
    organization = get_object_or_404(core_models.Organization, pk=organization_id)
    form = submission_forms.AuthorAffiliationForm(
        frozen_author=author,
        organization=organization,
        initial={"is_primary": not author.affiliations.exists()},
    )
    if request.method == "POST":
        form = submission_forms.AuthorAffiliationForm(
            request.POST,
            frozen_author=author,
            organization=organization,
        )
        if form.is_valid():
            affiliation = form.save()
            messages.add_message(
                request,
                messages.SUCCESS,
                _("Affiliation created: %(affiliation)s")
                % {"affiliation": affiliation},
            )
            return done(request, preprint, author)
    context = author_page_context(
        request, preprint, author, form=form, organization=organization
    )
    return render(request, "admin/core/affiliation_form.html", context)


@login_required
@transaction.atomic
def repository_affiliation_update(request, preprint_id, author_id, affiliation_id):
    preprint, author = get_preprint_author(request, preprint_id, author_id)
    affiliation = get_object_or_404(
        core_models.ControlledAffiliation,
        pk=affiliation_id,
        frozen_author=author,
    )
    form = submission_forms.AuthorAffiliationForm(
        instance=affiliation,
        frozen_author=author,
        organization=affiliation.organization,
    )
    if request.method == "POST":
        form = submission_forms.AuthorAffiliationForm(
            request.POST,
            instance=affiliation,
            frozen_author=author,
            organization=affiliation.organization,
        )
        if form.is_valid():
            form.save()
            messages.add_message(
                request,
                messages.SUCCESS,
                _("Affiliation updated: %(affiliation)s")
                % {"affiliation": affiliation},
            )
            return done(request, preprint, author)
    context = author_page_context(
        request,
        preprint,
        author,
        form=form,
        affiliation=affiliation,
        organization=affiliation.organization,
    )
    return render(request, "admin/core/affiliation_form.html", context)


@login_required
@transaction.atomic
def repository_affiliation_delete(request, preprint_id, author_id, affiliation_id):
    preprint, author = get_preprint_author(request, preprint_id, author_id)
    affiliation = get_object_or_404(
        core_models.ControlledAffiliation,
        pk=affiliation_id,
        frozen_author=author,
    )
    form = ConfirmDeleteForm()
    if request.method == "POST":
        form = ConfirmDeleteForm(request.POST)
        if form.is_valid():
            affiliation.delete()
            messages.add_message(
                request,
                messages.SUCCESS,
                _("Affiliation removed: %(affiliation)s")
                % {"affiliation": affiliation},
            )
            return done(request, preprint, author)
    context = author_page_context(
        request,
        preprint,
        author,
        form=form,
        affiliation=affiliation,
        organization=affiliation.organization,
        thing_to_delete=str(affiliation),
    )
    return render(request, "admin/core/affiliation_confirm_remove.html", context)


@login_required
@transaction.atomic
def repository_affiliation_update_from_orcid(
    request, preprint_id, author_id, how_many="primary"
):
    preprint, author = get_preprint_author(request, preprint_id, author_id)
    try:
        cleaned_orcid = clean_orcid_id(author.orcid)
    except ValueError:
        cleaned_orcid = None
    if not cleaned_orcid:
        messages.add_message(
            request,
            messages.WARNING,
            _(
                "%(author_name)s does not have an ORCID. Please re-add "
                "them by searching for their ORCID and try again."
            )
            % {"author_name": author.full_name()},
        )
        return done(request, preprint, author)

    orcid_details = orcid.get_orcid_record_details(cleaned_orcid)
    orcid_affils = (orcid_details or {}).get("affiliations", [])
    if not orcid_affils:
        messages.add_message(
            request,
            messages.WARNING,
            _(
                "No affiliations were found on the public ORCID record "
                "for ID %(orcid_id)s."
            )
            % {"orcid_id": cleaned_orcid},
        )
        return done(request, preprint, author)

    if how_many == "primary":
        orcid_affils = orcid_affils[:1]
    new_affils = []
    for orcid_affil in orcid_affils:
        orcid_affil_form = OrcidAffiliationForm(
            orcid_affil,
            tzinfo=request.user.preferred_timezone,
            data={"frozen_author": author},
        )
        if orcid_affil_form.is_valid():
            new_affils.append(orcid_affil_form.save(commit=False))

    form = ConfirmDeleteForm()
    if request.method == "POST":
        form = ConfirmDeleteForm(request.POST)
        if form.is_valid():
            author.affiliations.delete()
            for affil in new_affils:
                affil.save()
            messages.add_message(request, messages.SUCCESS, _("Affiliations updated."))
            return done(request, preprint, author)

    context = author_page_context(
        request,
        preprint,
        author,
        form=form,
        old_affils=author.affiliations,
        new_affils=new_affils,
    )
    return render(request, "admin/core/affiliation_update_from_orcid.html", context)
