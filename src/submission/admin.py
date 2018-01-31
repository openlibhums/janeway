__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
from django.contrib import admin

from hvad.admin import TranslatableAdmin

from submission import models


class FrozenAuthorAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'institution')
    search_fields = ('first_name', 'last_name')


class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'date_submitted', 'stage', 'owner', 'is_import', 'ithenticate_score')
    search_fields = ('title', 'subtitle')
    list_filter = ('stage', 'is_import')

    def get_queryset(self, request):
        return self.model.allarticles.get_queryset()


class ArticleLogAdmin(admin.ModelAdmin):
    list_display = ('article', 'stage_from', 'stage_to', 'date_time')
    readonly_fields = ('date_time',)


class LicenseAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_name', 'journal', 'url')
    list_filter = ('journal',)
    search_fields = ('name',)


class NoteAdmin(admin.ModelAdmin):
    list_display = ('article', 'creator', 'date_time')
    list_filter = ('article',)


class PublisherNoteAdmin(admin.ModelAdmin):
    list_display = ('creator', 'date_time', 'sequence')
    list_filter = ('creator',)


class KeywordAdmin(admin.ModelAdmin):
    list_display = ('word',)
    list_filter = ('word',)


class SectionAdmin(TranslatableAdmin):
    pass


admin_list = [
    (models.Article, ArticleAdmin),
    (models.Licence, LicenseAdmin),
    (models.Section, SectionAdmin),
    (models.ArticleStageLog, ArticleLogAdmin),
    (models.PublisherNote, PublisherNoteAdmin),
    (models.Note, NoteAdmin),
    (models.FrozenAuthor, FrozenAuthorAdmin),
    (models.Field,),
    (models.FieldAnswer,),
    (models.Keyword, KeywordAdmin),
]

[admin.site.register(*t) for t in admin_list]
