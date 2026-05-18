__copyright__ = "Copyright 2026 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"


from django.db.models import Count, Max, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from core import models as core_models
from review import models as review_models
from screening import models as screening_models


SCREENER_POOL_ROLES = ("editor", "section-editor")


def open_screening_round(article):
    """Open a new screening round for an article.

    Round numbers are sequential per article; the first round opens at 1
    and each subsequent round is one higher than the most recent round on
    that article.
    """
    existing = screening_models.ScreeningRound.objects.filter(article=article)
    if existing.exists():
        next_number = existing.order_by("-round_number").first().round_number + 1
    else:
        next_number = 1
    return screening_models.ScreeningRound.objects.create(
        article=article,
        round_number=next_number,
    )


def eligible_screeners(journal, exclude_user_ids=None):
    """Return Accounts eligible to act as screeners on the journal.

    If the journal has configured a ScreeningPool with one or more
    editorial groups selected, members of those groups make up the pool.
    Otherwise the pool falls back to holders of the editor or
    section-editor roles on this journal.
    """
    exclude_user_ids = set(exclude_user_ids or [])
    pool = screening_models.ScreeningPool.objects.filter(journal=journal).first()
    if pool is not None and pool.groups.exists():
        queryset = core_models.Account.objects.filter(
            editorialgroupmember__group__in=pool.groups.all(),
        )
    else:
        role_filter = core_models.AccountRole.objects.filter(
            role__slug__in=SCREENER_POOL_ROLES,
            journal=journal,
        )
        queryset = core_models.Account.objects.filter(
            accountrole__in=role_filter,
        )
    return queryset.exclude(pk__in=exclude_user_ids).distinct()


def assign_screener(
    article,
    screener,
    editor,
    screening_round,
    date_due,
    anonymous_to_author=True,
    anonymous_to_coscreeners=False,
    form=None,
):
    """Create a ScreeningAssignment for the given article and screener.

    Returns the assignment and a created boolean (matching Django's
    get_or_create signature).
    """
    return screening_models.ScreeningAssignment.objects.get_or_create(
        article=article,
        screener=screener,
        screening_round=screening_round,
        defaults={
            "editor": editor,
            "date_due": date_due,
            "anonymous_to_author": anonymous_to_author,
            "anonymous_to_coscreeners": anonymous_to_coscreeners,
            "form": form,
        },
    )


def current_screeners_on_round(screening_round):
    """Return the set of screener Accounts already assigned to this round."""
    return core_models.Account.objects.filter(
        screener_assignments__screening_round=screening_round,
    ).distinct()


def annotate_candidate_screeners(queryset, journal):
    """Decorate the candidate Account queryset with the per-row data the
    invitation table renders: editorial roles on this journal, current
    active screening count and the date of the screener's last completed
    screening on this journal."""
    annotated = queryset.annotate(
        active_screenings_count=Count(
            "screener_assignments",
            filter=Q(
                screener_assignments__article__journal=journal,
                screener_assignments__is_complete=False,
                screener_assignments__date_declined__isnull=True,
            ),
            distinct=True,
        ),
        last_screening_completed=Max(
            "screener_assignments__date_complete",
            filter=Q(
                screener_assignments__article__journal=journal,
                screener_assignments__is_complete=True,
            ),
        ),
    )
    role_lookup = editorial_role_labels_by_user(journal)
    group_lookup = editorial_group_labels_by_user(journal)
    candidates = list(annotated)
    for candidate in candidates:
        candidate.role_labels = role_lookup.get(candidate.pk, [])
        candidate.group_labels = group_lookup.get(candidate.pk, [])
    return candidates


def editorial_role_labels_by_user(journal):
    """Return a mapping of user_id -> [role display name, ...] for the
    editorial team on the journal. Keeps the per-candidate role list to
    a single query rather than touching account_role for every row."""
    role_qs = core_models.AccountRole.objects.filter(
        journal=journal,
        role__slug__in=SCREENER_POOL_ROLES,
    ).select_related("role")
    mapping = {}
    for row in role_qs:
        mapping.setdefault(row.user_id, []).append(row.role.name)
    return mapping


def editorial_group_labels_by_user(journal):
    """Return a mapping of user_id -> [editorial group name, ...] for
    members of the groups in this journal's screener pool. Falls back
    to an empty mapping when no pool is configured."""
    pool = screening_models.ScreeningPool.objects.filter(journal=journal).first()
    if pool is None:
        return {}
    members = core_models.EditorialGroupMember.objects.filter(
        group__in=pool.groups.all(),
    ).select_related("group")
    mapping = {}
    for member in members:
        mapping.setdefault(member.user_id, []).append(member.group.name)
    return mapping


def back_url_for_assignment(request, assignment):
    """Return the URL the user should be sent to after viewing or
    completing a screening report. Editors go back to the article's
    screening page; screeners go back to their Screening Requests list."""
    if request.user.pk == assignment.screener_id:
        return reverse("screening_requests")
    return reverse(
        "screening_article",
        kwargs={"article_id": assignment.article_id},
    )


def setup_after_screening(article, next_element):
    """Per-stage setup when an article exits screening into the next
    workflow element. Mirrors editor_assignment's dispatcher so that
    going screening → review still creates ReviewRound 1, etc."""
    if next_element.element_name == "review":
        review_models.ReviewRound.objects.get_or_create(
            article=article,
            round_number=1,
        )


def get_open_revision_for_author(request, revision_id):
    """Return the open ScreeningRevisionRequest belonging to the
    correspondence author on the current journal, raising Http404 if
    the user is not the corresponding author or the revision is not
    open."""
    revision = get_object_or_404(
        screening_models.ScreeningRevisionRequest,
        pk=revision_id,
        article__journal=request.journal,
        date_completed__isnull=True,
    )
    if request.user != revision.article.correspondence_author:
        raise Http404
    return revision


def render_checklist_item_response(request, item):
    """Return the appropriate response for a checklist-item mutation:
    a single-row HTML partial when the request is from HTMX (so the
    table can swap just the affected row), or a full-page redirect
    back to the screening article otherwise."""
    if request.headers.get("HX-Request"):
        return render(
            request,
            "admin/screening/_checklist_item_row.html",
            {"item": item},
        )
    return redirect(
        reverse(
            "screening_article",
            kwargs={"article_id": item.checklist.article.pk},
        )
    )


def ensure_checklist_for_article(article):
    """Return the article's TechnicalChecklist, creating one from the
    journal's default template if none exists yet. Returns None if the
    journal has no default checklist template configured."""
    existing = screening_models.TechnicalChecklist.objects.filter(
        article=article,
    ).first()
    if existing:
        return existing

    default_template = screening_models.TechnicalChecklistTemplate.objects.filter(
        journal=article.journal,
        is_default=True,
        deleted=False,
    ).first()
    if default_template is None:
        return None

    checklist = screening_models.TechnicalChecklist.objects.create(
        article=article,
        template=default_template,
    )
    for template_item in default_template.items.all():
        screening_models.TechnicalChecklistItem.objects.create(
            checklist=checklist,
            template_item=template_item,
            label=template_item.label,
            order=template_item.order,
        )
    return checklist
