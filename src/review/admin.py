__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.contrib import admin
from review import models


class EditorialAdmin(admin.ModelAdmin):
    list_display = ('pk', 'article', 'editor', 'editor_type', 'assigned')
    list_filter = ('article', 'editor', 'editor_type')
    raw_id_fields = ('article', 'editor')


class ReviewRoundAdmin(admin.ModelAdmin):
    list_display = ('pk', 'article', 'round_number', 'date_started')
    list_filter = ('article',)
    raw_id_fields = ('article',)
    filter_horizontal = ('review_files',)


class ReviewAdmin(admin.ModelAdmin):
    list_display = ('pk', 'article', 'reviewer', 'editor', 'review_round', 'decision', 'date_due', 'is_complete')
    list_filter = ('article', 'reviewer', 'editor')
    raw_id_fields = ('article', 'reviewer', 'editor', 'review_round', 'form', 'review_file')


class ReviewFormAdmin(admin.ModelAdmin):
    list_display = ('name', 'journal', 'slug', 'deleted')
    list_filter = ('journal', 'deleted')
    filter_horizontal = ('elements',)


class ElementAdmin(admin.ModelAdmin):
    list_display = ('name', 'kind', 'required', 'order', 'width')


class AnswerAdmin(admin.ModelAdmin):
    list_display = ('pk', 'assignment', 'frozen_element', 'author_can_see')
    list_filter = ('assignment',)
    raw_id_fields = ('assignment',)


class RatingAdmin(admin.ModelAdmin):
    list_display = ('pk', 'reviewer', 'rating', 'rater')
    list_filter = ('assignment', 'rater')
    raw_id_fields = ('assignment', 'rater')

    def reviewer(self, obj):
        return obj.assignment.reviewer


class RevisionActionAdmin(admin.ModelAdmin):
    list_display = ('pk', 'logged', 'user')


class RevisionAdmin(admin.ModelAdmin):
    list_display = ('pk', 'article', 'editor', 'date_requested', 'date_due')
    list_filter = ('article', 'editor')
    raw_id_fields = ('article', 'editor')
    filter_horizontal = ('actions',)


class EditorOverrideAdmin(admin.ModelAdmin):
    list_display = ('pk', 'article', 'editor', 'overwritten')
    list_filter = ('article', 'editor')
    raw_id_fields = ('article', 'editor')


class DraftAdmin(admin.ModelAdmin):
    list_display = ('pk', 'article', 'section_editor', 'decision', 'drafted', 'editor_decision')
    list_filter = ('article', 'section_editor', 'decision', 'editor_decision')
    raw_id_fields = ('article', 'section_editor')


admin_list = [
    (models.EditorAssignment, EditorialAdmin),
    (models.ReviewAssignment, ReviewAdmin),
    (models.ReviewForm, ReviewFormAdmin),
    (models.ReviewFormElement, ElementAdmin),
    (models.ReviewAssignmentAnswer, AnswerAdmin),
    (models.ReviewRound, ReviewRoundAdmin),
    (models.ReviewerRating, RatingAdmin),
    (models.RevisionAction, RevisionActionAdmin),
    (models.RevisionRequest, RevisionAdmin),
    (models.EditorOverride, EditorOverrideAdmin),
    (models.DecisionDraft, DraftAdmin),
]

[admin.site.register(*t) for t in admin_list]
