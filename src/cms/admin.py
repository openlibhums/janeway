__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.contrib import admin
from cms import models


class NavigationItemAdmin(admin.ModelAdmin):
    list_display = ('link_name', 'link', 'is_external',
                    'sequence', 'top_level_nav', 'has_sub_nav',
                    'object', 'content_type')
    list_filter = ('is_external', 'top_level_nav', 'has_sub_nav', 'content_type', 'link_name', 'link', )
    search_fields = ('link_name', 'link')


class PageAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'name', 'edited', 'object', 'content_type')
    list_filter = ('display_name', 'name', 'content_type')
    date_hierarchy = ('edited')
    search_fields = ('display_name', 'name')
    view_on_site = True


class SubmissionItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'journal', 'order')
    list_filter = ('journal',)
    raw_id_fields = ('journal', 'existing_setting')
    search_fields = ('title', )


class MediaFileAdmin(admin.ModelAdmin):
    list_display = ('label', 'journal', 'uploaded', 'file')
    list_filter = ('journal', )
    date_hierarchy = ('uploaded')
    search_fields = ('label', 'journal__code', 'file')


admin_list = [
    (models.NavigationItem, NavigationItemAdmin),
    (models.Page, PageAdmin),
    (models.SubmissionItem, SubmissionItemAdmin),
    (models.MediaFile, MediaFileAdmin),
]

[admin.site.register(*t) for t in admin_list]
