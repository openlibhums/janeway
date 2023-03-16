__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.contrib import admin
from utils import admin_utils
from comms import models


class TagAdmin(admin.ModelAdmin):
    list_display = ('text', '_count')
    search_fields = ('text',)

    def _count(self, obj):
        return obj.tags.count()

    inlines = [
        admin_utils.NewsItemInline,
    ]


class NewsItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'posted', 'posted_by',
                    'start_display', 'end_display', 'object')
    list_filter = (admin_utils.GenericRelationJournalFilter,
                   admin_utils.GenericRelationPressFilter,
                   'posted', 'start_display', 'end_display')
    search_fields = ('title', 'body', 'tags__text', 'posted_by__email',
                     'posted_by__first_name', 'posted_by__last_name',
                     'custom_byline')
    date_hierarchy = ('posted')
    filter_horizontal = ('tags',)
    raw_id_fields = ('posted_by', 'large_image_file')


admin_list = [
    (models.NewsItem, NewsItemAdmin),
    (models.Tag, TagAdmin),
]

[admin.site.register(*t) for t in admin_list]
