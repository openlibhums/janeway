__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.contrib import admin
from hvad.admin import TranslatableAdmin

from utils import models


class SettingValueAdmin(TranslatableAdmin):
    pass


class ImportCacheAdmin(admin.ModelAdmin):
    list_display = ('url', 'mime_type', 'date_time')
    list_filter = ('url', 'mime_type')


admin_list = [
    (models.LogEntry,),
    (models.Plugin,),
    (models.PluginSetting,),
    (models.PluginSettingValue, SettingValueAdmin),
    (models.ImportCacheEntry, ImportCacheAdmin),
]

[admin.site.register(*t) for t in admin_list]
