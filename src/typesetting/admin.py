__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.contrib import admin
from django.template.defaultfilters import truncatewords_html

from typesetting import admin_utils as typesetting_admin_utils
from typesetting import models
from utils import admin_utils as utils_admin_utils


class TypesettingClaimAdmin(utils_admin_utils.ArticleFKModelAdmin):
    list_display = ('_article', 'editor', 'claimed', '_journal')
    list_filter = ('article__journal', 'claimed')
    date_hierarchy = ('claimed')
    search_fields = ('editor__email', 'editor__first_name',
                     'editor__last_name', 'article__pk',
                     'article__title')
    raw_id_fields = ('article', 'editor')


class TypesettingRoundAdmin(utils_admin_utils.ArticleFKModelAdmin):
    list_display = ('_article', '_journal', 'round_number', 'date_created')
    list_filter = ('article__journal', 'round_number', 'date_created')
    search_fields = ('article__pk', 'article__title')
    raw_id_fields = ('article',)
    date_hierarchy = ('date_created')

    inlines = [
        typesetting_admin_utils.TypesettingAssignmentInline,
        typesetting_admin_utils.GalleyProofingInline,
    ]


class TypesettingAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        '_article',
        '_journal',
        'round',
        'typesetter',
        'manager',
        'assigned',
        'friendly_status',
    )
    list_filter = (
        'round__article__journal',
        'round__round_number',
    )
    raw_id_fields = (
        'typesetter',
        'manager',
        'round',
        'files_to_typeset',
        'galleys_created',
    )
    search_fields = (
        'round__article__pk',
        'round__article__title',
        'typesetter__email',
        'typesetter__first_name',
        'typesetter__last_name',
        'manager__email',
        'manager__first_name',
        'manager__last_name',
        'task',
        'typesetter_note',
    )
    date_hierarchy = ('assigned')

    inlines = [
        typesetting_admin_utils.TypesettingCorrectionInline,
    ]

    def _article(self, obj):
        return truncatewords_html(
            str(obj.round.article), 10
        ) if obj else ''

    def _journal(self, obj):
        return obj.round.article.journal if obj else ''


class GalleyProofingAdmin(admin.ModelAdmin):
    list_display = (
        '_article',
        '_journal',
        'round',
        'proofreader',
        'manager',
        'assigned',
    )
    list_filter = (
        'round__article__journal',
        'round',
        'assigned',
    )
    raw_id_fields = (
        'proofreader',
        'manager',
        'round',
        'proofed_files',
        'annotated_files',
    )
    search_fields = (
        'round__article__pk',
        'round__article__title',
        'proofreader__email',
        'proofreader__first_name',
        'proofreader__last_name',
        'manager__email',
        'manager__first_name',
        'manager__last_name',
        'task',
        'notes',
    )
    date_hierarchy = ('assigned')

    def _article(self, obj):
        return truncatewords_html(
            str(obj.round.article), 10
        ) if obj else ''

    def _journal(self, obj):
        return obj.round.article.journal if obj else ''


class TypesettingCorrectionAdmin(admin.ModelAdmin):
    list_display = (
        'task',
        'galley',
        'label',
        'status',
        'date_requested',
        'date_completed',
        'date_declined',
        '_journal',
    )
    list_filter = (
        'task__round__article__journal',
        'date_requested',
        'date_completed',
        'date_declined',
    )
    raw_id_fields = (
        'galley',
        'task',
    )
    search_fields = (
        'task__round__article__pk',
        'task__round__article__title',
        'task__manager__email',
        'task__manager__first_name',
        'task__manager__last_name',
        'task__typesetter__email',
        'task__typesetter__first_name',
        'task__typesetter__last_name',
    )

    def _journal(self, obj):
        return obj.task.round.article.journal if obj else ''


admin_list = [
    (models.TypesettingClaim, TypesettingClaimAdmin),
    (models.TypesettingRound, TypesettingRoundAdmin),
    (models.TypesettingAssignment, TypesettingAssignmentAdmin),
    (models.GalleyProofing, GalleyProofingAdmin),
    (models.TypesettingCorrection, TypesettingCorrectionAdmin),
]

[admin.site.register(*t) for t in admin_list]
