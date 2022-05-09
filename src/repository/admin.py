__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.contrib import admin
from repository import models


class RepositoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'pk', 'live')
    list_filter = ('live',)
    search_fields = ('name',)
    filter_horizontal = ('managers',)


class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'repository', 'enabled', 'parent')
    list_filter = ('enabled',)
    search_fields = ('name', 'slug')
    filter_horizontal = ('editors',)


class PreprintAdmin(admin.ModelAdmin):
    list_display = ('title', 'pk', 'repository', 'doi', 'current_version')
    list_filter = ('repository',)
    raw_id_fields = ('repository', 'owner', 'subject', 'article', 'submission_file')
    filter_horizontal = ('keywords',)

    save_as = True


class VersionAdmin(admin.ModelAdmin):
    list_display = ('pk', 'preprint', 'title', 'version', 'date_time')
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


class PreprintFileAdmin(admin.ModelAdmin):
    list_display = ('preprint', 'file')
    list_filter = ('preprint',)
    raw_id_fields = ('preprint',)


class PreprintAccessAdmin(admin.ModelAdmin):
    list_display = ('preprint', 'accessed', 'country', 'access_type')
    list_filter = ('preprint', 'country')
    save_as = True


class PreprintAuthorAdmin(admin.ModelAdmin):
    list_display = ('account', 'preprint', 'order')
    list_filter = ('account', 'preprint',)
    raw_id_fields = ('preprint', 'preprint')


class PreprintSupplementaryFileAdmin(admin.ModelAdmin):
    pass


class RepositoryRoleAdmin(admin.ModelAdmin):
    list_display = ('pk', 'repository', 'user', 'role')
    list_filter = ('repository', 'role')
    raw_id_fields = ('repository', 'user', 'role')


class ReviewAdmin(admin.ModelAdmin):
    list_display = ('pk', 'reviewer', 'manager', 'preprint',)
    raw_id_fields = ('preprint', 'manager', 'reviewer', 'comment')
    list_display_links = ('pk', 'reviewer')


admin_list = [
    (models.Repository, RepositoryAdmin),
    (models.PreprintVersion, VersionAdmin),
    (models.Comment, CommentAdmin),
    (models.Subject, SubjectAdmin),
    (models.VersionQueue, QueueAdmin),
    (models.Preprint, PreprintAdmin),
    (models.PreprintFile, PreprintFileAdmin),
    (models.PreprintSupplementaryFile, PreprintSupplementaryFileAdmin),
    (models.PreprintAuthor, PreprintAuthorAdmin),
    (models.RepositoryField,),
    (models.RepositoryFieldAnswer,),
    (models.PreprintAccess, PreprintAccessAdmin),
    (models.Review, ReviewAdmin),
    (models.RepositoryRole, RepositoryRoleAdmin)

]

[admin.site.register(*t) for t in admin_list]
