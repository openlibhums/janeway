__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django.contrib import admin
from copyediting import models


class CopyeditAdmin(admin.ModelAdmin):
    list_display = ('pk', 'article', 'copyeditor', 'editor', 'assigned',
                    'due', 'decision', 'date_decided', 'copyedit_reopened')
    list_filter = ('copyeditor', 'editor', 'article')
    search_fields = ('article__title',)
    filter_horizontal = ('files_for_copyediting', 'copyeditor_files')
    raw_id_fields = ('article', 'copyeditor', 'editor')


class AuthorAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'author', 'assigned', 'notified', 'decision',
                    'date_decided')
    list_filter = ('author',)
    raw_id_fields = ('author', 'assignment')
    filter_horizontal = ('files_updated',)


admin_list = [
    (models.CopyeditAssignment, CopyeditAdmin),
    (models.AuthorReview, AuthorAdmin),
]

[admin.site.register(*t) for t in admin_list]
