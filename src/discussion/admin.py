__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve, Andy Byers & Mauro Sanchez"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.contrib import admin
from discussion import models


class PostInline(admin.TabularInline):
    model = models.Post
    extra = 0
    raw_id_fields = ('owner', 'thread')
    exclude = ('read_by',)


class ThreadAdmin(admin.ModelAdmin):
    list_display = ('pk', 'subject', 'owner', 'started', 'object_title')
    list_filter = ('subject', 'started', 'last_updated')
    search_fields = ('pk', 'article__title', 'preprint__title',
                     'subject', 'owner__first_name', 'owner__last_name',
                     'owner__email', 'post__body')
    raw_id_fields = ('owner', 'article', 'preprint')
    date_hierarchy = ('last_updated')

    inlines = [
        PostInline
    ]


class PostAdmin(admin.ModelAdmin):
    list_display = ('pk', 'thread', 'owner', 'posted',)
    search_fields = ('pk', 'body', 'thread__subject', 'owner__first_name',
                     'owner__last_name', 'owner__email',)
    raw_id_fields = ('thread', 'owner',)
    filter_horizontal = ('read_by',)
    save_as = True
    date_hierarchy = ('posted')


admin_list = [
    (models.Thread, ThreadAdmin),
    (models.Post, PostAdmin),
]

[admin.site.register(*t) for t in admin_list]
