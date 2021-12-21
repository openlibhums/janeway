__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve, Andy Byers & Mauro Sanchez"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.contrib import admin
from discussion import models


class ThreadAdmin(admin.ModelAdmin):
    list_display = ('pk', 'subject', 'owner', 'started', 'object_title')
    raw_id_fields = ('owner', 'article', 'preprint')


class PostAdmin(admin.ModelAdmin):
    list_display = ('pk', 'thread', 'owner', 'posted',)
    raw_id_fields = ('thread', 'owner',)
    filter_horizontal = ('read_by',)
    save_as = True


admin_list = [
    (models.Thread, ThreadAdmin),
    (models.Post, PostAdmin),
]

[admin.site.register(*t) for t in admin_list]