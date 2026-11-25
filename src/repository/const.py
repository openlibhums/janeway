"""
Constants defined by the repository app
"""

from django.db.models import Q
from django.utils.translation import gettext_lazy as _

TAB_DATE_LABELS = {
    "date_started": _("Started"),
    "date_submitted": _("Submitted"),
    "date_accepted": _("Accepted"),
    "date_published": _("Published"),
    "date_declined": _("Declined"),
}

TAB_ICONS = {
    "new": "fa-inbox",
    "accepted": "fa-check",
    "published": "fa-globe",
    "rejected": "fa-ban",
    "drafts": "fa-pencil",
    "review": "fa-hourglass-half",
}

UNPUBLISHED = Q(date_published__isnull=True, date_declined__isnull=True)

MANAGER_TABS = [
    ("new", _("New"), UNPUBLISHED & Q(date_accepted__isnull=True), "date_submitted"),
    (
        "accepted",
        _("Accepted"),
        UNPUBLISHED & Q(date_accepted__isnull=False),
        "date_accepted",
    ),
    ("published", _("Published"), Q(date_published__isnull=False), "date_published"),
    (
        "rejected",
        _("Rejected"),
        Q(date_published__isnull=True, date_declined__isnull=False),
        "date_declined",
    ),
]

AUTHOR_TABS = [
    ("drafts", _("Drafts"), Q(date_submitted__isnull=True), "date_started"),
    (
        "review",
        _("Under consideration"),
        Q(date_submitted__isnull=False) & UNPUBLISHED,
        "date_submitted",
    ),
    ("published", _("Published"), Q(date_published__isnull=False), "date_published"),
    (
        "rejected",
        _("Rejected"),
        Q(date_published__isnull=True, date_declined__isnull=False),
        "date_declined",
    ),
]
