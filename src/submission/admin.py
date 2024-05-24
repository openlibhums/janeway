__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.contrib import admin
from django import forms
from django.template.defaultfilters import truncatewords_html

from utils import admin_utils
from submission import models


class LicenseChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.short_name


class FunderAdmin(admin.ModelAdmin):
    list_display = ('name', 'fundref_id', 'funding_id')
    list_filter = ('article__journal',)
    search_fields = ('name', 'fundref_id', 'funding_id')

    inlines = [
        admin_utils.FundersArticleInline,
    ]

class FrozenAuthorAdmin(admin_utils.ArticleFKModelAdmin):
    list_display = ('pk', 'first_name', 'last_name',
                    'frozen_email', 'frozen_orcid', 'institution', '_journal')
    list_filter = ('article__journal',)
    search_fields = ('frozen_email', 'frozen_orcid',
                     'first_name', 'last_name',
                     'institution', 'frozen_biography', )
    raw_id_fields = ('article', 'author',)


class ArticleAdmin(admin_utils.JanewayModelAdmin):
    list_display = ('pk', 'title', 'correspondence_author',
                    'journal', 'date_submitted', 'stage',
                    'owner', 'is_import')
    search_fields = (
        'pk',
        'title',
        'correspondence_author__email',
        'correspondence_author__first_name',
        'correspondence_author__last_name',
        'owner__email',
        'owner__first_name',
        'owner__last_name',
    )
    list_filter = (
        'journal',
        'stage',
        'is_import',
        'peer_reviewed',
        'date_submitted',
        'date_accepted',
        'date_declined',
        'date_published',
        'date_updated',
        'last_modified',
    )
    raw_id_fields = (
        'section',
        'owner',
        'license',
        'authors',
        'correspondence_author',
        'primary_issue',
        'projected_issue',
        'render_galley',
        'large_image_file',
        'thumbnail_image_file',
        'preprint_journal_article',
        'source_files',
        'manuscript_files',
        'data_figure_files',
        'supplementary_files',
        'publisher_notes',
        'funders',
    )
    filter_horizontal = (
        'authors',
        'keywords',
    )

    inlines = [
        admin_utils.IdentifierInline,
        admin_utils.NoteInline,
        admin_utils.FieldAnswerInline,
        admin_utils.KeywordArticleInline,
        admin_utils.GalleyInline,
        admin_utils.ArticleStageLogInline,
        admin_utils.WorkflowLogInline,
        admin_utils.CronTaskInline,
    ]

    def get_queryset(self, request):
        return self.model.objects.get_queryset()


class ArticleLogAdmin(admin_utils.ArticleFKModelAdmin):
    list_display = ('_article', '_journal', 'stage_from',
                    'stage_to', 'date_time')
    list_filter = ('article__journal', 'stage_from', 'stage_to')
    search_fields = ('article__pk', 'article__title',
                     'stage_from', 'stage_to')
    date_hierarchy = ('date_time')
    readonly_fields = ('date_time',)

    def _article(self, obj):
        return truncatewords_html(str(obj.article), 10) if obj else ''


class LicenseAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_name', 'journal', 'url', '_text')
    list_filter = ('journal', 'short_name', 'url')
    search_fields = ('name', 'short_name', 'url', 'text')

    def _text(self, obj):
        return truncatewords_html(obj.text, 8) if obj else ''


class NoteAdmin(admin_utils.ArticleFKModelAdmin):
    list_display = ('_text', '_article', '_journal', 'creator', 'date_time')
    list_filter = ('article__journal', 'date_time',)
    raw_id_fields = ('article', 'creator')
    date_hierarchy = ('date_time')
    search_fields = ('text', 'article__pk', 'article__title',
                     'creator__email', 'creator__first_name',
                     'creator__last_name')
    raw_id_fields = ('creator',)

    def _text(self, obj):
        return truncatewords_html(obj.text, 10) if obj else ''

    def _article(self, obj):
        return truncatewords_html(str(obj.article), 10) if obj else ''


class PublisherNoteAdmin(admin.ModelAdmin):
    list_display = ('_text', 'creator', 'date_time', 'sequence')
    list_filter = ('date_time',)
    date_hierarchy = ('date_time')
    search_fields = ('text', 'creator__email', 'creator__first_name',
                     'creator__last_name')
    raw_id_fields = ('creator',)

    def _text(self, obj):
        return truncatewords_html(obj.text, 10) if obj else ''


class KeywordAdmin(admin.ModelAdmin):
    list_display = ('word',)
    list_filter = ('keywordarticle__article__journal',)
    search_fields = ('word',)

    inlines = [
        admin_utils.KeywordArticleInline,
    ]


class SectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'journal', 'article_count',
                    'number_of_reviewers', 'is_filterable',
                    'public_submissions', 'indexing')
    list_filter = ('journal', 'is_filterable', 'public_submissions',
                   'indexing')
    search_fields = ('name',)
    raw_id_fields = ('editors', 'section_editors')

    @staticmethod
    def apply_select_related(self, qs):
        return qs.prefetch_related('journal')


class FieldAdmin(admin.ModelAdmin):
    list_display = ('name', 'journal', 'press', 'kind',
                    'width', 'required', 'display')
    list_filter = ('journal', 'press', 'kind', 'width',
                   'required', 'display')
    search_fields = ('name', 'help_text', 'choices')


class FieldAnswerAdmin(admin_utils.ArticleFKModelAdmin):
    list_display = ('field', '_answer', '_article', '_journal')
    list_filter = ('article__journal',)
    search_fields = ('field__name', 'article__pk', 'article__title',
                     'answer')

    def _answer(self, obj):
        return truncatewords_html(obj.answer, 10) if obj else ''


class SubmissionConfigAdmin(admin.ModelAdmin):
    list_display = ('pk', 'journal',
                    'copyright_notice', 'competing_interests',
                    'comments_to_the_editor', 'abstract',
                    'language', 'license', 'keywords', 'section',
                    'figures_data', 'default_license',
                    'default_language', 'default_section',
                    'submission_file_text')
    raw_id_fields = ('default_license', 'default_section')


class ArticleAuthorOrderAdmin(admin_utils.ArticleFKModelAdmin):
    list_display = ('order', '_article', 'author', '_journal')
    list_filter = ('article__journal', 'order')
    search_fields = ('article__pk', 'article__title', 'author__email',
                     'author__first_name', 'author__last_name')
    raw_id_fields = ('article', 'author')


admin_list = [
    (models.Funder, FunderAdmin),
    (models.Article, ArticleAdmin),
    (models.Licence, LicenseAdmin),
    (models.Section, SectionAdmin),
    (models.ArticleStageLog, ArticleLogAdmin),
    (models.PublisherNote, PublisherNoteAdmin),
    (models.Note, NoteAdmin),
    (models.FrozenAuthor, FrozenAuthorAdmin),
    (models.Field, FieldAdmin),
    (models.FieldAnswer, FieldAnswerAdmin),
    (models.Keyword, KeywordAdmin),
    (models.SubmissionConfiguration, SubmissionConfigAdmin),
    (models.ArticleAuthorOrder, ArticleAuthorOrderAdmin),
]

[admin.site.register(*t) for t in admin_list]
