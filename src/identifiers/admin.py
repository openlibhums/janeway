__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.contrib import admin
from utils import admin_utils
from identifiers import models
from journal import models as journal_models


class BrokenDOIAdmin(admin.ModelAdmin):
    list_display = ('identifier', 'resolves_to', 'expected_to_resolve_to',
                    'checked', 'journal')
    list_filter = ('identifier__article__journal', 'checked')
    raw_id_fields = ('article', 'identifier')
    search_fields = ('identifier__identifier', 'identifier__article__pk',
                     'identifier__article__title')
    date_hierarchy = ('checked')

    def journal(self, obj):
        return obj.identifier.article.journal if obj else ''


class IdentifierAdmin(admin_utils.ArticleFKModelAdmin):
    list_display = ('pk', 'id_type', 'identifier',
                    'registration_status', 'article_url', 'article', 'journal')
    list_filter = ('article__journal', 'id_type')
    list_display_links = ('identifier', )
    search_fields = ('pk', 'id_type', 'identifier', 'article__title')
    raw_id_fields = ('article',)

    def article_url(self, obj):
        return obj.article.url if obj else ''

    def registration_status(self, obj):
        if obj and obj.crossrefstatus:
            return obj.crossrefstatus.get_message_display()
        else:
            return ''

    inlines = [
        admin_utils.IdentifierCrossrefStatusInline,
    ]


class CrossrefStatusAdmin(admin.ModelAdmin):
    list_display = ('pk', 'message', 'identifier', 'latest_deposit', 'journal')
    list_filter = ('identifier__article__journal', 'message')
    list_display_links = ('message', )
    search_fields = ('pk', 'identifier__identifier', 'message')
    raw_id_fields = ('identifier',)
    readonly_fields = ('deposits', 'message')

    def journal(self, obj):
        return obj.identifier.article.journal if obj else ''


class CrossrefDepositAdmin(admin.ModelAdmin):
    list_display = ('pk', 'file_name', 'has_result', 'queued',
                    'success', 'citation_success',
                    'date_time', 'polling_attempts', 'journal')
    list_filter = ('crossrefstatus__identifier__article__journal',
                   'has_result', 'queued', 'success', 'citation_success',
                   'date_time', 'polling_attempts')
    search_fields = ('pk', 'file_name', 'document', 'result_text')
    date_hierarchy = ('date_time')

    def journal(self, obj):
        return obj.journal if obj else ''

    inlines = [
        admin_utils.DepositCrossrefStatusInline,
    ]


admin_list = [
    (models.Identifier, IdentifierAdmin),
    (models.BrokenDOI, BrokenDOIAdmin),
    (models.CrossrefStatus, CrossrefStatusAdmin),
    (models.CrossrefDeposit, CrossrefDepositAdmin),
]

[admin.site.register(*t) for t in admin_list]
