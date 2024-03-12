__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django.contrib import admin
from utils import admin_utils
from copyediting import models


class CopyeditAdmin(admin_utils.ArticleFKModelAdmin):
    list_display = ('pk', '_article', 'copyeditor', 'editor', 'assigned',
                    'decision', 'due', '_journal')
    list_filter = ('article__journal', 'assigned', 'due', 'date_decided',
                   'copyedit_reopened', 'decision')
    search_fields = ('article__title', 'copyeditor__first_name',
                     'copyeditor__last_name', 'copyeditor__email',
                     'editor__first_name', 'editor__last_name',
                     'editor__email', 'editor_note', 'copyeditor_note')
    raw_id_fields = ('article', 'copyeditor', 'editor')
    filter_horizontal = ('files_for_copyediting', 'copyeditor_files')

    inlines = [
        admin_utils.AuthorReviewInline
    ]


class AuthorAdmin(admin.ModelAdmin):
    list_display = ('pk', 'author', 'assigned',
                    'assignment', '_journal')
    list_filter = ('assignment__article__journal', 'assigned',
                   'notified', 'date_decided', 'decision')
    search_fields = ('assignment__article__title', 'author__first_name',
                     'author__last_name', 'author__email',
                     'assignment__editor_note', 'assignment__copyeditor_note')
    raw_id_fields = ('author', 'assignment')
    filter_horizontal = ('files_updated',)
    exclude = ('files_updated',)

    def _journal(self, obj):
        return obj.assignment.article.journal.code if obj else ''


admin_list = [
    (models.CopyeditAssignment, CopyeditAdmin),
    (models.AuthorReview, AuthorAdmin),
]

[admin.site.register(*t) for t in admin_list]
