__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.contrib import admin
from identifiers import models


class BrokenDOIAdmin(admin.ModelAdmin):
    list_display = ('identifier', 'resolves_to', 'expected_to_resolve_to', 'checked')
    raw_id_fields = ('article', 'identifier')


class IdentifierAdmin(admin.ModelAdmin):
    list_display = ('pk', 'id_type', 'identifier', 'enabled', 'article')
    raw_id_fields = ('article',)


class CrossrefStatusAdmin(admin.ModelAdmin):
    list_display = ('pk', 'identifier', 'message', 'latest_deposit')
    search_fields = ('pk', 'identifier__identifier', )
    list_filter = ('message',)


class CrossrefDepositAdmin(admin.ModelAdmin):
    list_display = ('pk', 'file_name', 'document', 'has_result',
                    'result_text', 'success',
                    'queued', 'citation_success',
                    'date_time', 'polling_attempts')
    search_fields = ('pk', 'file_name', 'document', 'result_text')
    list_filter = ('date_time',)


admin_list = [
    (models.Identifier, IdentifierAdmin),
    (models.BrokenDOI, BrokenDOIAdmin),
    (models.CrossrefStatus, CrossrefStatusAdmin),
    (models.CrossrefDeposit, CrossrefDepositAdmin),
]

[admin.site.register(*t) for t in admin_list]
