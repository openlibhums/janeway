__copyright__ = "Copyright 2026 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"

from django.contrib import admin

from screening import models
from utils import admin_utils


class ScreeningRoundAdmin(admin_utils.ArticleFKModelAdmin):
    list_display = ("pk", "_article", "round_number", "date_started", "_journal")
    list_filter = ("article__journal", "round_number", "date_started")
    search_fields = ("article__pk", "article__title", "article__journal__code")
    raw_id_fields = ("article",)
    date_hierarchy = "date_started"


class ScreeningAssignmentAdmin(admin_utils.ArticleFKModelAdmin):
    list_display = (
        "pk",
        "_article",
        "_journal",
        "screener",
        "editor",
        "recommendation",
        "anonymous_to_author",
        "anonymous_to_coscreeners",
        "date_due",
        "date_complete",
        "is_complete",
    )
    list_filter = (
        "article__journal",
        "recommendation",
        "anonymous_to_author",
        "anonymous_to_coscreeners",
        "is_complete",
        "date_due",
    )
    search_fields = (
        "article__pk",
        "article__title",
        "screener__email",
        "screener__first_name",
        "screener__last_name",
        "editor__email",
        "editor__first_name",
        "editor__last_name",
    )
    raw_id_fields = (
        "article",
        "screener",
        "editor",
        "screening_round",
        "form",
    )
    date_hierarchy = "date_requested"


class ScreeningFormAdmin(admin.ModelAdmin):
    list_display = ("pk", "name", "journal", "deleted")
    list_filter = ("journal", "deleted")
    search_fields = ("name", "journal__code")
    raw_id_fields = ("elements",)


class ScreeningFormElementAdmin(admin.ModelAdmin):
    list_display = ("pk", "name", "kind", "required", "order")
    list_filter = ("kind", "required")
    search_fields = ("name",)


class FrozenScreeningFormElementAdmin(admin.ModelAdmin):
    list_display = ("pk", "name", "kind", "order", "answer")
    list_filter = ("kind",)
    search_fields = ("name",)
    raw_id_fields = ("form_element", "answer")


class ScreeningAssignmentAnswerAdmin(admin.ModelAdmin):
    list_display = ("pk", "assignment", "original_element")
    raw_id_fields = ("assignment", "original_element")


class ScreeningRevisionRequestAdmin(admin_utils.ArticleFKModelAdmin):
    list_display = (
        "pk",
        "_article",
        "_journal",
        "editor",
        "type",
        "date_requested",
        "date_due",
        "date_completed",
    )
    list_filter = ("type", "article__journal", "date_due")
    search_fields = (
        "article__pk",
        "article__title",
        "editor__email",
    )
    raw_id_fields = ("article", "editor")
    date_hierarchy = "date_requested"


admin_list = [
    (models.ScreeningRound, ScreeningRoundAdmin),
    (models.ScreeningAssignment, ScreeningAssignmentAdmin),
    (models.ScreeningForm, ScreeningFormAdmin),
    (models.ScreeningFormElement, ScreeningFormElementAdmin),
    (models.FrozenScreeningFormElement, FrozenScreeningFormElementAdmin),
    (models.ScreeningAssignmentAnswer, ScreeningAssignmentAnswerAdmin),
    (models.ScreeningRevisionRequest, ScreeningRevisionRequestAdmin),
]

[admin.site.register(*t) for t in admin_list]
