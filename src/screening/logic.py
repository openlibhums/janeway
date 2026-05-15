__copyright__ = "Copyright 2026 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"


from core import models as core_models
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
