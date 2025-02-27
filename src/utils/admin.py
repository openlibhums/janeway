__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.contrib import admin

from utils import admin_utils
from utils import models


class ImportCacheAdmin(admin.ModelAdmin):
    list_display = ('url', 'mime_type', 'date_time')
    list_filter = ('mime_type',)
    search_fields = ('url', 'on_disk')
    date_hierarchy = ('date_time')


class PluginAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_name', 'version', 'date_installed',
                    'enabled', 'press_wide')
    list_filter = ('name', 'display_name', 'version', 'date_installed',
                   'enabled', 'press_wide')
    search_fields = ('name', 'display_name')
    date_hierarchy = ('date_installed')


class LogAdmin(admin.ModelAdmin):
    list_display = ('pk', 'types', 'date', 'level', 'actor', '_to',
                    'is_email', 'email_subject', 'target')
    list_filter = (admin_utils.GenericRelationArticleJournalFilter,
                   admin_utils.GenericRelationPreprintRepositoryFilter,
                   'date', 'is_email', 'types', 'addressee__field')
    search_fields = ('types', 'email_subject', 'actor__email',
                     'actor__first_name', 'actor__last_name',
                     'ip_address', 'email_subject', 'addressee__email')
    date_hierarchy = ('date')
    raw_id_fields = ('actor',)

    inlines = [
        admin_utils.AddresseeInline,
    ]

    def _to(self, obj):
        if obj:
            return ", ".join([to.email for to in obj.addressee_set.all()])


class VersionAdmin(admin.ModelAdmin):
    list_display = ('number', 'date', 'rollback')
    list_filter = ('number', 'date', 'rollback')
    search_fields = ('number',)
    date_hierarchy = ('date')


class RORImportAdmin(admin.ModelAdmin):
    list_display = ('pk', 'status', 'started', 'stopped')
    list_filter = ('status', 'started', 'stopped')
    search_fields = ('rorimporterror__message', 'records',)
    date_hierarchy = ('started')
    readonly_fields = ('started', 'stopped', 'status', 'records')
    inlines = [
        admin_utils.RORImportErrorInline,
    ]


class RORImportErrorAdmin(admin.ModelAdmin):
    list_display = ('pk', '_first_line')
    search_fields = ('message',)
    date_hierarchy = ('ror_import__started')
    raw_id_fields = ('ror_import', )

    def _first_line(self, obj):
        return obj.message.split('\n')[0] if obj and obj.message else ''


admin_list = [
    (models.LogEntry, LogAdmin),
    (models.Plugin, PluginAdmin),
    (models.ImportCacheEntry, ImportCacheAdmin),
    (models.Version, VersionAdmin),
    (models.RORImport, RORImportAdmin),
    (models.RORImportError, RORImportErrorAdmin),
]

[admin.site.register(*t) for t in admin_list]
