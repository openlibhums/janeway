__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.contrib import admin
from utils import admin_utils
from cms import models
from simple_history.admin import SimpleHistoryAdmin


class NavigationItemAdmin(admin.ModelAdmin):
    list_display = ('link_name', 'link', 'is_external',
                    'sequence', 'top_level_nav', 'has_sub_nav',
                    'object')
    list_filter = (admin_utils.GenericRelationJournalFilter,
                   admin_utils.GenericRelationPressFilter,
                   'is_external', 'top_level_nav', 'has_sub_nav')
    search_fields = ('link_name', 'link')
    raw_id_fields = ('page', 'top_level_nav')


class PageAdmin(SimpleHistoryAdmin):
    list_display = ('display_name', 'name', 'edited', 'object')
    list_filter = (admin_utils.GenericRelationJournalFilter,
                   admin_utils.GenericRelationPressFilter,
                   'edited')
    date_hierarchy = ('edited')
    search_fields = ('display_name', 'name', 'content')


class SubmissionItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'journal', 'order')
    list_filter = ('journal',)
    raw_id_fields = ('journal', 'existing_setting')
    search_fields = ('title', 'journal__code', 'text')


class MediaFileAdmin(admin.ModelAdmin):
    list_display = ('label', 'journal', 'uploaded', 'file')
    list_filter = ('journal', 'uploaded')
    date_hierarchy = ('uploaded')
    search_fields = ('label', 'file')


admin_list = [
    (models.NavigationItem, NavigationItemAdmin),
    (models.Page, PageAdmin),
    (models.SubmissionItem, SubmissionItemAdmin),
    (models.MediaFile, MediaFileAdmin),
]

[admin.site.register(*t) for t in admin_list]
