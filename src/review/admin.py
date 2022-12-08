__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.contrib import admin
from utils import admin_utils
from review import models
from core.templatetags.truncate import truncatesmart


class EditorialAdmin(admin.ModelAdmin):
    list_display = ('pk', 'article', 'journal', 'editor',
                    'editor_type', 'assigned', 'notified')
    list_filter = ('article__journal', 'editor_type', 'assigned', 'notified')
    search_fields = ('article__pk', 'article__title', 'article__journal__code',
                     'editor__email', 'editor__first_name',
                     'editor__last_name',)
    raw_id_fields = ('article', 'editor')
    date_hierarchy = ('assigned')

    def journal(self, obj):
        return obj.article.journal.code if obj else ''


class ReviewRoundAdmin(admin.ModelAdmin):
    list_display = ('pk', 'article', 'round_number', 'date_started',
                    'journal')
    list_filter = ('article__journal', 'round_number', 'date_started')
    search_fields = ('article__pk', 'article__title', 'article__journal__code')
    raw_id_fields = ('article',)
    filter_horizontal = ('review_files',)
    date_hierarchy = ('date_started')

    def journal(self, obj):
        return obj.article.journal.code if obj else ''


class ReviewAdmin(admin.ModelAdmin):
    list_display = ('pk', '_article', 'journal', 'reviewer', 'editor',
                    'round', 'decision', 'date_requested', 'is_complete')
    list_filter = ('article__journal', 'review_round__round_number',
                   'decision', 'is_complete',
                   'date_requested', 'date_accepted',
                   'date_declined', 'date_complete', 'date_reminded',
                   'date_due')
    search_fields = ('article__pk', 'article__title', 'article__journal__code',
                     'editor__email', 'editor__first_name',
                     'editor__last_name',
                     'reviewer__email', 'reviewer__first_name',
                     'reviewer__last_name',
                     'competing_interests', 'comments_for_editor')
    date_hierarchy = ('date_requested')
    raw_id_fields = ('article', 'reviewer', 'editor', 'review_round',
                     'form', 'review_file')

    def journal(self, obj):
        return obj.article.journal.code if obj else ''

    def round(self, obj):
        return obj.review_round.round_number if obj else ''

    def _article(self, obj):
        return truncatesmart(str(obj.article), 30) if obj else ''

    inlines = [
        admin_utils.ReviewAssignmentAnswerInline,
    ]


class ReviewFormAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'journal', 'deleted')
    list_filter = ('journal', 'deleted')
    filter_horizontal = ('elements',)
    search_fields = ('name', 'slug', 'journal__code',
                     'intro', 'thanks')


class ElementAdmin(admin.ModelAdmin):
    list_display = ('name', 'kind', 'required', 'order', 'width')
    list_filter = ('kind', 'required')
    search_fields = ('name', 'help_text')


class FrozenReviewFormElementAdmin(admin.ModelAdmin):
    list_display = ('name', 'kind', 'required', 'order', 'width')
    list_filter = ('kind', 'required')
    search_fields = ('name', 'help_text')
    raw_id_fields = ('form_element', 'answer',)


class AnswerAdmin(admin.ModelAdmin):
    list_display = ('pk', 'element_answer', 'assignment', 'frozen_element',
                    'author_can_see')
    list_display_links = ('element_answer',)
    list_filter = ('assignment__article__journal', 'assignment__date_complete',
                   'assignment__date_due')
    search_fields = ('assignment__article__pk', 'assignment__article__title',
                     'assignment__reviewer__email',
                     'assignment__reviewer__first_name',
                     'assignment__reviewer__last_name',
                     'answer', 'edited_answer')
    raw_id_fields = ('assignment',)
    date_hierarchy = ('assignment__date_complete')

    def element_answer(self, obj):
        return truncatesmart(obj.answer, 25) if obj else ''


class RatingAdmin(admin.ModelAdmin):
    list_display = ('pk', 'reviewer', 'rating', 'rater', 'journal',
                    'assignment')
    list_filter = ('assignment__article__journal__code', 'rating')
    search_fields = ('assignment__article__pk', 'assignment__article__title',
                     'assignment__reviewer__email',
                     'assignment__reviewer__first_name',
                     'assignment__reviewer__last_name',
                     'rater__email', 'rater__first_name',
                     'rater__last_name',)
    raw_id_fields = ('assignment', 'rater')
    date_hierarchy = ('assignment__date_complete')

    def reviewer(self, obj):
        return obj.assignment.reviewer

    def journal(self, obj):
        return obj.assignment.article.journal.code if obj else ''


class RevisionActionAdmin(admin.ModelAdmin):
    list_display = ('pk', 'logged', 'user', 'action_text')
    raw_id_fields = ('user',)
    search_fields = ('user__email', 'user__first_name',
                     'user__last_name', 'text')
    date_hierarchy = ('logged')

    def action_text(self, obj):
        return truncatesmart(obj.text, 30) if obj else ''


class RevisionAdmin(admin.ModelAdmin):
    list_display = ('pk', '_article', 'journal', 'editor', '_editor_note',
                    'author', '_author_note', 'date_requested')
    list_filter = ('article__journal', 'type', 'date_requested',
                   'date_completed', 'date_due')
    search_fields = ('article__pk', 'article__title', 'article__journal__code',
                     'editor__email', 'editor__first_name',
                     'editor__last_name',
                     'article__correspondence_author__email',
                     'article__correspondence_author__first_name',
                     'article__correspondence_author__last_name',
                     'editor_note', 'author_note')
    raw_id_fields = ('article', 'editor')
    filter_horizontal = ('actions',)
    date_hierarchy = ('date_requested')

    def journal(self, obj):
        return obj.article.journal.code if obj else ''

    def _article(self, obj):
        return truncatesmart(str(obj.article), 30) if obj else ''

    def _editor_note(self, obj):
        return truncatesmart(str(obj.editor_note), 30) if obj else ''

    def author(self, obj):
        return obj.article.correspondence_author if obj else ''

    def _author_note(self, obj):
        return truncatesmart(str(obj.author_note), 30) if obj else ''


class EditorOverrideAdmin(admin.ModelAdmin):
    list_display = ('pk', 'article', 'journal', 'editor', 'overwritten')
    list_filter = ('article__journal', 'overwritten')
    search_fields = ('article__pk', 'article__title', 'article__journal__code',
                     'editor__email', 'editor__first_name',
                     'editor__last_name',
                     'article__correspondence_author__email',
                     'article__correspondence_author__first_name',
                     'article__correspondence_author__last_name')
    raw_id_fields = ('article', 'editor')

    def journal(self, obj):
        return obj.article.journal.code if obj else ''


class DraftAdmin(admin.ModelAdmin):
    list_display = ('pk', '_article', 'journal', 'section_editor', 'decision',
                    'drafted', 'editor', 'editor_decision')
    list_filter = ('article__journal', 'decision', 'editor_decision',
                   'drafted', 'revision_request_due_date')
    search_fields = ('article__pk', 'article__title', 'article__journal__code',
                     'editor__email', 'editor__first_name',
                     'editor__last_name',
                     'section_editor__email', 'section_editor__first_name',
                     'section_editor__last_name',
                     'article__correspondence_author__email',
                     'article__correspondence_author__first_name',
                     'article__correspondence_author__last_name',
                     'message_to_editor', 'email_message',
                     'editor_decline_rationale')
    raw_id_fields = ('article', 'editor', 'section_editor')
    date_hierarchy = ('drafted')

    def journal(self, obj):
        return obj.article.journal.code if obj else ''

    def _article(self, obj):
        return truncatesmart(str(obj.article), 30) if obj else ''


admin_list = [
    (models.EditorAssignment, EditorialAdmin),
    (models.ReviewAssignment, ReviewAdmin),
    (models.ReviewForm, ReviewFormAdmin),
    (models.ReviewFormElement, ElementAdmin),
    (models.FrozenReviewFormElement, FrozenReviewFormElementAdmin),
    (models.ReviewAssignmentAnswer, AnswerAdmin),
    (models.ReviewRound, ReviewRoundAdmin),
    (models.ReviewerRating, RatingAdmin),
    (models.RevisionAction, RevisionActionAdmin),
    (models.RevisionRequest, RevisionAdmin),
    (models.EditorOverride, EditorOverrideAdmin),
    (models.DecisionDraft, DraftAdmin),
]

[admin.site.register(*t) for t in admin_list]
