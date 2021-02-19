__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.contrib import admin
from django import forms

from submission import models


class LicenseChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.short_name


class FrozenAuthorAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'institution')
    search_fields = ('first_name', 'last_name')


class ArticleAdmin(admin.ModelAdmin):
    list_display = ('pk', 'title', 'journal', 'date_submitted', 'stage',
                    'owner', 'is_import', 'ithenticate_score')
    search_fields = ('pk', 'title', 'subtitle')
    list_filter = ('stage', 'is_import', 'journal')
    raw_id_fields = (
        'section',
        'owner',
        'license',
        'correspondence_author',
        'primary_issue',
        'projected_issue',
    )
    filter_horizontal = (
        'authors',
        'manuscript_files',
        'data_figure_files',
        'supplementary_files',
        'publisher_notes',
        'keywords',
        'source_files',
    )

    def get_queryset(self, request):
        return self.model.allarticles.get_queryset()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'license':
            return LicenseChoiceField(queryset=models.Licence.objects.all().order_by('journal__code'))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class ArticleLogAdmin(admin.ModelAdmin):
    list_display = ('article', 'stage_from', 'stage_to', 'date_time')
    list_filter = ('article', 'stage_from', 'stage_to')
    readonly_fields = ('date_time',)


class LicenseAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_name', 'journal', 'url')
    list_filter = ('journal',)
    search_fields = ('name',)


class NoteAdmin(admin.ModelAdmin):
    list_display = ('article', 'creator', 'date_time')
    list_filter = ('article',)
    raw_id_fields = ('article', 'creator')


class PublisherNoteAdmin(admin.ModelAdmin):
    list_display = ('creator', 'date_time', 'sequence')
    list_filter = ('creator',)


class KeywordAdmin(admin.ModelAdmin):
    list_display = ('word',)
    search_fields = ('word',)


class SectionAdmin(admin.ModelAdmin):
    list_display = ('section_name', 'section_journal', 'number_of_reviewers', 'is_filterable', 'public_submissions',
                    'indexing')
    list_filter = ('journal',)

    @staticmethod
    def apply_select_related(self, qs):
        return qs.prefetch_related('journal')

    def section_journal(self, obj):
        return obj.journal

    def section_name(self, obj):
        return obj.name


class FieldAdmin(admin.ModelAdmin):
    list_display = ('name', 'journal', 'press', 'kind', 'width', 'required')
    list_filter = ('journal', 'press', 'kind', 'width')


class SubmissionConfigAdmin(admin.ModelAdmin):
    list_display = ('journal', 'publication_fees', 'submission_check', 'copyright_notice', 'competing_interests',
                    'comments_to_the_editor', 'subtitle', 'abstract', 'language', 'license', 'keywords',
                    'figures_data')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'default_license':
            return LicenseChoiceField(queryset=models.Licence.objects.all().order_by('journal__code'))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class ArticleAuthorOrderAdmin(admin.ModelAdmin):
    list_display = ('order', 'article', 'author',)
    list_filter = ('article',)
    search_fields = ('article__pk', 'article__title',)


admin_list = [
    (models.Article, ArticleAdmin),
    (models.Licence, LicenseAdmin),
    (models.Section, SectionAdmin),
    (models.ArticleStageLog, ArticleLogAdmin),
    (models.PublisherNote, PublisherNoteAdmin),
    (models.Note, NoteAdmin),
    (models.FrozenAuthor, FrozenAuthorAdmin),
    (models.Field, FieldAdmin),
    (models.FieldAnswer,),
    (models.Keyword, KeywordAdmin),
    (models.SubmissionConfiguration, SubmissionConfigAdmin),
    (models.ArticleAuthorOrder, ArticleAuthorOrderAdmin),
]

[admin.site.register(*t) for t in admin_list]
