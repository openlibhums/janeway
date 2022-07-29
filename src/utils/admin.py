__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.contrib import admin

from utils import models


class ImportCacheAdmin(admin.ModelAdmin):
    list_display = ('url', 'mime_type', 'date_time')
    list_filter = ('url', 'mime_type')


class PluginAdmin(admin.ModelAdmin):
    list_display = ('name', 'version', 'date_installed', 'enabled', 'display_name', 'press_wide')


class LogAdmin(admin.ModelAdmin):
    list_display = ('pk', 'types', 'date', 'level', 'actor', 'ip_address', 'is_email', 'target')


class VersionAdmin(admin.ModelAdmin):
    list_display = ('number', 'date', 'rollback')


admin_list = [
    (models.LogEntry, LogAdmin),
    (models.Plugin, PluginAdmin),
    (models.ImportCacheEntry, ImportCacheAdmin),
    (models.Version, VersionAdmin)
]

[admin.site.register(*t) for t in admin_list]
