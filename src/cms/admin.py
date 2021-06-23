__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.contrib import admin
from cms import models


class PageAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'name', 'object')


class SubmissionItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'journal', 'order')
    list_filter = ('journal',)
    raw_id_fields = ('journal', 'existing_setting')


admin_list = [
    (models.NavigationItem,),
    (models.Page, PageAdmin),
    (models.SubmissionItem, SubmissionItemAdmin),
]

[admin.site.register(*t) for t in admin_list]
