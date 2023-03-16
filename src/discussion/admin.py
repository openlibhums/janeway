__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve, Andy Byers & Mauro Sanchez"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.contrib import admin
from django.template.defaultfilters import truncatewords_html
from utils import admin_utils
from discussion import models


class ThreadAdmin(admin_utils.ArticleFKModelAdmin):
    list_display = ('pk', 'subject', 'owner', 'started', 'object_title',
                    '_journal')
    list_filter = ('article__journal', 'subject', 'started', 'last_updated')
    search_fields = ('pk', 'article__title', 'preprint__title',
                     'subject', 'owner__first_name', 'owner__last_name',
                     'owner__email', 'post__body')
    raw_id_fields = ('owner', 'article', 'preprint')

    inlines = [
        admin_utils.PostInline
    ]


class PostAdmin(admin.ModelAdmin):
    list_display = ('_post', 'thread', 'owner', 'posted', '_journal')
    list_filter = ('thread__article__journal', 'posted')
    search_fields = ('pk', 'body', 'thread__subject', 'owner__first_name',
                     'owner__last_name', 'owner__email',)
    raw_id_fields = ('thread', 'owner',)
    filter_horizontal = ('read_by',)
    save_as = True
    date_hierarchy = ('posted')

    def _post(self, obj):
        return truncatewords_html(obj.body, 10) if obj else ''

    def _journal(self, obj):
        return obj.thread.article.journal if obj else ''


admin_list = [
    (models.Thread, ThreadAdmin),
    (models.Post, PostAdmin),
]

[admin.site.register(*t) for t in admin_list]
