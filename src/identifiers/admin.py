__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.contrib import admin
from identifiers import models


class CrossrefStatusInline(admin.TabularInline):
    model = models.CrossrefStatus
    extra = 0
    filter_horizontal = ('deposits',)


class BrokenDOIAdmin(admin.ModelAdmin):
    list_display = ('identifier', 'resolves_to', 'expected_to_resolve_to', 'checked')
    raw_id_fields = ('article', 'identifier')


class IdentifierAdmin(admin.ModelAdmin):
    list_display = ('pk', 'id_type', 'identifier',
                    'registration_status', 'article_url', 'article')
    list_display_links = ('identifier', )
    search_fields = ('pk', 'id_type', 'identifier', 'article__title')
    raw_id_fields = ('article',)

    def article_url(self, obj):
        if obj:
            return obj.article.url
        else:
            return ''

    def registration_status(self, obj):
        if obj and obj.crossrefstatus:
            return obj.crossrefstatus.get_message_display()
        else:
            return ''

    inlines = [
        CrossrefStatusInline,
    ]


class CrossrefStatusAdmin(admin.ModelAdmin):
    list_display = ('pk', 'message', 'identifier', 'latest_deposit')
    list_display_links = ('message', )
    search_fields = ('pk', 'identifier__identifier', 'message')
    list_filter = ('message',)


class CrossrefDepositAdmin(admin.ModelAdmin):
    list_display = ('pk', 'file_name', 'has_result', 'queued',
                    'success', 'citation_success',
                    'date_time', 'polling_attempts')
    list_filter = ('has_result', 'queued', 'success', 'citation_success',
                   'date_time', 'polling_attempts')
    search_fields = ('pk', 'file_name', 'document', 'result_text')
    date_hierarchy = ('date_time')


admin_list = [
    (models.Identifier, IdentifierAdmin),
    (models.BrokenDOI, BrokenDOIAdmin),
    (models.CrossrefStatus, CrossrefStatusAdmin),
    (models.CrossrefDeposit, CrossrefDepositAdmin),
]

[admin.site.register(*t) for t in admin_list]
