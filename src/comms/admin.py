__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.contrib import admin
from comms import models


class TagAdmin(admin.ModelAdmin):
    list_display = ('text',)
    search_fields = ('text',)


class NewsItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'object', 'posted', 'posted_by', 'start_display', 'end_display')
    list_filter = ('posted', 'start_display', 'end_display', 'content_type')
    search_fields = ('title', 'body', 'tag__text', 'posted_by__email', 'posted_by__first_name', 'posted_by__last_name', 'custom_byline')
    date_hierarchy = ('posted')


admin_list = [
    (models.NewsItem, NewsItemAdmin),
    (models.Tag, TagAdmin),
]

[admin.site.register(*t) for t in admin_list]
