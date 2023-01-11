__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.contrib import admin

from plugins.typesetting import admin_utils
from plugins.typesetting import models


class TypesettingClaimAdmin(admin.ModelAdmin):
    list_display = ('article', 'editor', 'claimed', 'journal')
    list_filter = ('article__journal', 'claimed')
    date_hierarchy = ('claimed')
    search_fields = ('editor__email', 'editor__first_name',
                     'editor__last_name', 'article__pk',
                     'article__title')
    raw_id_fields = ('article', 'editor')

    def journal(self, obj):
        return obj.article.journal.code if obj else ''


class TypesettingRoundAdmin(admin.ModelAdmin):
    list_display = ('article', 'journal', 'round_number', 'date_created')
    list_filter = ('article__journal', 'round_number', 'date_created')
    search_fields = ('article__pk', 'article__title')
    raw_id_fields = ('article',)
    date_hierarchy = ('date_created')

    def journal(self, obj):
        return obj.article.journal.code if obj else ''

    inlines = [
        admin_utils.TypesettingAssignmentInline,
        admin_utils.GalleyProofingInline,
    ]


class TypesettingAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        'article',
        'journal',
        'round',
        'typesetter',
        'manager',
        'assigned',
        'friendly_status',
    )
    list_filter = (
        'round__article__journal',
        'round',
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
        admin_utils.TypesettingCorrectionInline,
    ]

    def article(self, obj):
        return obj.round.article if obj else ''

    def journal(self, obj):
        return obj.round.article.journal.code if obj else ''


class GalleyProofingAdmin(admin.ModelAdmin):
    list_display = (
        'article',
        'journal',
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

    def article(self, obj):
        return obj.round.article if obj else ''

    def journal(self, obj):
        return obj.round.article.journal.code if obj else ''


class TypesettingCorrectionAdmin(admin.ModelAdmin):
    list_display = (
        'task',
        'galley',
        'label',
        'status',
        'date_requested',
        'date_completed',
        'date_declined',
        'journal',
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

    def article(self, obj):
        return obj.task.round.article if obj else ''

    def journal(self, obj):
        return obj.task.round.article.journal.code if obj else ''


admin_list = [
    (models.TypesettingClaim, TypesettingClaimAdmin),
    (models.TypesettingRound, TypesettingRoundAdmin),
    (models.TypesettingAssignment, TypesettingAssignmentAdmin),
    (models.GalleyProofing, GalleyProofingAdmin),
    (models.TypesettingCorrection, TypesettingCorrectionAdmin),
]

[admin.site.register(*t) for t in admin_list]
