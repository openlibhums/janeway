__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.contrib import admin
from preprint import models


class RepositoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'pk', 'live')
    list_filter = ('live',)
    search_fields = ('name',)
    filter_horizontal = ('managers',)

class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'enabled')
    list_filter = ('enabled',)
    search_fields = ('name', 'slug')
    filter_horizontal = ('editors',)


class PreprintAdmin(admin.ModelAdmin):
    list_display = ('title', 'pk', 'repository', 'doi', 'curent_version')
    list_filter = ('repository',)
    raw_id_fields = ('repository',)
    filter_horizontal = ('keywords',)


class VersionAdmin(admin.ModelAdmin):
    list_display = ('pk', 'preprint', 'version', 'date_time')
    list_filter = ('preprint',)
    raw_id_fields = ('preprint',)


class CommentAdmin(admin.ModelAdmin):
    list_display = ('pk', 'preprint', 'author', 'date_time', 'is_reviewed', 'is_public')
    list_filter = ('preprint', 'author', 'is_reviewed', 'is_public')
    raw_id_fields = ('preprint', 'author', 'reply_to',)


class QueueAdmin(admin.ModelAdmin):
    list_display = ('pk', 'preprint', 'file', 'update_type', 'date_submitted', 'approved', 'date_decision')
    list_filter = ('preprint', 'update_type', 'approved')
    raw_id_fields = ('preprint', 'file',)


admin_list = [
    (models.PreprintVersion, VersionAdmin),
    (models.Comment, CommentAdmin),
    (models.Subject, SubjectAdmin),
    (models.VersionQueue, QueueAdmin),
    (models.Preprint, PreprintAdmin),
]

[admin.site.register(*t) for t in admin_list]
