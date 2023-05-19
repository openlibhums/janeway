__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.contrib import admin
from django.template.defaultfilters import truncatewords, truncatewords_html
from utils import admin_utils
from review import models


class EditorialAdmin(admin_utils.ArticleFKModelAdmin):
    list_display = ('pk', '_article', '_journal', 'editor',
                    'editor_type', 'assigned', 'notified')
    list_filter = ('article__journal', 'editor_type', 'assigned', 'notified')
    search_fields = ('article__pk', 'article__title', 'article__journal__code',
                     'editor__email', 'editor__first_name',
                     'editor__last_name',)
    raw_id_fields = ('article', 'editor')
    date_hierarchy = ('assigned')


class ReviewRoundAdmin(admin_utils.ArticleFKModelAdmin):
    list_display = ('pk', '_article', 'round_number', 'date_started',
                    '_journal')
    list_filter = ('article__journal', 'round_number', 'date_started')
    search_fields = ('article__pk', 'article__title', 'article__journal__code')
    raw_id_fields = ('article', 'review_files',)
    date_hierarchy = ('date_started')


class ReviewAdmin(admin_utils.ArticleFKModelAdmin):
    list_display = ('pk', '_article', '_journal', 'reviewer', 'editor',
                    '_round', 'decision', 'date_requested', 'is_complete')
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
    raw_id_fields = ('article', 'reviewer', 'editor', 'review_round',
                     'form', 'review_file')

    def _round(self, obj):
        return obj.review_round.round_number if obj else ''

    inlines = [
        admin_utils.ReviewAssignmentAnswerInline,
    ]


class ReviewFormAdmin(admin.ModelAdmin):
    list_display = ('name', 'journal', 'deleted')
    list_filter = ('journal', 'deleted')
    filter_horizontal = ('elements',)
    search_fields = ('name', 'journal__code',
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
    list_display = ('pk', '_element_answer', 'assignment', 'frozen_element',
                    'author_can_see', '_journal')
    list_display_links = ('_element_answer',)
    list_filter = ('assignment__article__journal', 'assignment__date_complete',
                   'assignment__date_due')
    search_fields = ('assignment__article__pk', 'assignment__article__title',
                     'assignment__reviewer__email',
                     'assignment__reviewer__first_name',
                     'assignment__reviewer__last_name',
                     'answer', 'edited_answer')
    raw_id_fields = ('assignment',)

    def _element_answer(self, obj):
        return truncatewords_html(obj.answer, 5) if obj else ''

    def _journal(self, obj):
        return obj.assignment.article.journal if obj else ''


class RatingAdmin(admin.ModelAdmin):
    list_display = ('pk', '_reviewer', 'rating', 'rater', '_journal',
                    '_assignment')
    list_filter = ('assignment__article__journal', 'rating')
    search_fields = ('assignment__article__pk', 'assignment__article__title',
                     'assignment__reviewer__email',
                     'assignment__reviewer__first_name',
                     'assignment__reviewer__last_name',
                     'rater__email', 'rater__first_name',
                     'rater__last_name',)
    raw_id_fields = ('assignment', 'rater')
    date_hierarchy = ('assignment__date_complete')

    def _reviewer(self, obj):
        return obj.assignment.reviewer

    def _journal(self, obj):
        return obj.assignment.article.journal.code if obj else ''

    def _assignment(self, obj):
        return truncatewords(obj.assignment.__str__(), 10) if obj else ''


class RevisionActionAdmin(admin.ModelAdmin):
    list_display = ('pk', 'logged', 'user', '_action_text')
    raw_id_fields = ('user',)
    search_fields = ('user__email', 'user__first_name',
                     'user__last_name', 'text')
    date_hierarchy = ('logged')

    def _action_text(self, obj):
        return truncatewords(obj.text, 5) if obj else ''


class RevisionAdmin(admin_utils.ArticleFKModelAdmin):
    list_display = ('pk', '_article', '_journal', 'editor', '_editor_note',
                    '_author', '_author_note', 'date_requested')
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

    inlines = [
        admin_utils.RevisionActionInline,
    ]

    def _editor_note(self, obj):
        return truncatewords_html(str(obj.editor_note), 5) if obj else ''

    def _author_note(self, obj):
        return truncatewords_html(str(obj.author_note), 5) if obj else ''


class EditorOverrideAdmin(admin_utils.ArticleFKModelAdmin):
    list_display = ('pk', '_article', '_journal', 'editor', 'overwritten')
    list_filter = ('article__journal', 'overwritten')
    search_fields = ('article__pk', 'article__title', 'article__journal__code',
                     'editor__email', 'editor__first_name',
                     'editor__last_name',
                     'article__correspondence_author__email',
                     'article__correspondence_author__first_name',
                     'article__correspondence_author__last_name')
    raw_id_fields = ('article', 'editor')


class DraftAdmin(admin_utils.ArticleFKModelAdmin):
    list_display = ('pk', '_article', '_journal', 'section_editor', 'decision',
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
