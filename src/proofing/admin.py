__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.contrib import admin
from proofing import models


class ProofingAssignmentAdmin(admin.ModelAdmin):
    list_display = ('pk', 'article', 'proofing_manager', 'editor', 'assigned', 'completed')
    list_filter = ('proofing_manager', 'editor')
    raw_id_fields = ('article', 'proofing_manager', 'editor')


class ProofingRound(admin.ModelAdmin):
    list_display = ('pk', 'assignment', 'number', 'date_started')
    list_filter = ('assignment',)
    raw_id_fields = ('assignment',)


class ProofingTaskAdmin(admin.ModelAdmin):
    list_display = ('pk', 'round', 'proofreader', 'assigned', 'due', 'accepted', 'completed', 'cancelled')
    list_filter = ('round', 'proofreader')
    raw_id_fields = ('round', 'proofreader')
    filter_horizontal = ('galleys_for_proofing', 'notes')


class CorrectionTaskAdmin(admin.ModelAdmin):
    list_display = ('pk', 'proofing_task', 'typesetter', 'assigned', 'due', 'accepted', 'completed')
    list_filter = ('proofing_task', 'typesetter')
    raw_id_fields = ('proofing_task', 'typesetter')
    filter_horizontal = ('galleys',)


class NoteAdmin(admin.ModelAdmin):
    list_display = ('pk', 'galley', 'creator', 'date_time')
    list_filter = ('galley', 'creator')
    search_fields = ('text',)
    raw_id_fields = ('galley', 'creator')


admin_list = [
    (models.ProofingAssignment, ProofingAssignmentAdmin),
    (models.ProofingRound, ProofingRound),
    (models.ProofingTask, ProofingTaskAdmin),
    (models.TypesetterProofingTask, CorrectionTaskAdmin),
    (models.Note, NoteAdmin),
]

[admin.site.register(*t) for t in admin_list]
