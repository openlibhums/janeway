__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.contrib import admin
from django.template.defaultfilters import truncatewords_html
from simple_history.admin import SimpleHistoryAdmin

from repository import models
from utils import admin_utils


class RepositoryAdmin(SimpleHistoryAdmin):
    list_display = ('pk', 'short_name', 'name', 'live')
    list_display_links = ('short_name', 'name')
    list_filter = ('live',)
    search_fields = ('short_name', 'name',)
    raw_id_fields = ('managers', 'homepage_preprints',
                     'active_licenses')

    inlines = [
        admin_utils.RepositoryRoleInline,
    ]


class RepositoryRoleAdmin(admin.ModelAdmin):
    list_display = ('pk', 'repository', 'user', 'role')
    list_filter = ('repository', 'role')
    search_fields = ('repository__name', 'repository__short_name',
                     'user__email', 'user__first_name',
                     'user__last_name', 'role__slug',
                     'role__name')
    raw_id_fields = ('repository', 'user', 'role')


class RepositoryFieldAdmin(admin.ModelAdmin):
    list_display = ('name', 'input_type', 'required', 'display',
                    'dc_metadata_type', 'repository')
    list_filter = ('repository__short_name', 'input_type',
                   'required', 'display', 'dc_metadata_type')
    search_fields = ('name', 'help_text', 'dc_metadata_type', 'choices')


class RepositoryFieldAnswerAdmin(admin.ModelAdmin):
    list_display = ('_answer', 'field', 'preprint', '_repository')
    list_filter = ('field__repository__short_name', 'field')
    search_fields = ('answer', 'preprint__title', 'preprint__pk')
    raw_id_fields = ('field',)

    def _answer(self, obj):
        return truncatewords_html(obj.answer, 10) if obj else ''

    def _repository(self, obj):
        return obj.field.repository if obj else ''


class PreprintAdmin(admin.ModelAdmin):
    list_display = ('pk', 'title', 'owner', 'repository',
                    'date_submitted', 'doi', 'current_version')
    list_display_links = ('pk', 'title')
    list_filter = ('repository__short_name', 'date_started',
                   'date_submitted', 'date_accepted', 'date_declined',
                   'date_published', 'date_updated', 'current_step')
    raw_id_fields = ('repository', 'owner', 'subject',
                     'article', 'submission_file', 'license')
    search_fields = ('pk', 'title', 'owner__email', 'owner__orcid',
                     'owner__first_name', 'owner__last_name', 'abstract',
                     'submission_file__original_filename', 'subject__name',
                     'comments_editor', 'doi', 'preprint_doi',
                     'preprint_decline_note', 'article__pk', 'article__title')
    filter_horizontal = ('keywords',)
    date_hierarchy = ('date_submitted')

    inlines = [
        admin_utils.PreprintAuthorInline,
        admin_utils.RepositoryFieldAnswerInline,
        admin_utils.RepositoryReviewInline,
        admin_utils.PreprintVersionInline,
        admin_utils.VersionQueueInline,
        admin_utils.PreprintFileInline,
        admin_utils.PreprintSupplementaryFileInline,
        admin_utils.KeywordPreprintInline,
        admin_utils.CommentInline,
    ]

    save_as = True


class KeywordPreprintAdmin(admin_utils.PreprintFKModelAdmin):
    list_display = ('keyword', '_preprint', 'order', '_repository')
    list_filter = ('preprint__repository__short_name',)
    raw_id_fields = ('keyword', 'preprint')
    search_fields = ('keyword__word', 'preprint__pk', 'preprint__title',)


class PreprintFileAdmin(admin_utils.PreprintFKModelAdmin):
    list_display = ('_preprint', 'file', 'original_filename', 'uploaded',
                    '_repository')
    list_filter = ('preprint__repository__short_name', 'uploaded', 'mime_type')
    raw_id_fields = ('preprint',)
    search_fields = ('preprint__pk', 'preprint__title', 'original_filename')
    date_hierarchy = ('uploaded')


class PreprintSupplementaryFileAdmin(admin_utils.PreprintFKModelAdmin):
    list_display = ('_preprint', 'url', 'label', 'order', '_repository')
    list_filter = ('preprint__repository__short_name',)
    search_fields = ('preprint__pk', 'preprint__title', 'url', 'label')


class PreprintAccessAdmin(admin_utils.PreprintFKModelAdmin):
    list_display = ('_preprint', 'file', 'accessed', 'access_type', 'country',
                    '_repository')
    list_filter = ('preprint__repository__short_name', 'accessed',
                   'country')
    search_fields = ('preprint__pk', 'preprint__title', 'identifier',
                     'file__original_filename')
    raw_id_fields = ('preprint',)
    save_as = True


class PreprintAuthorAdmin(admin_utils.PreprintFKModelAdmin):
    list_display = ('pk', '_preprint', 'account', 'order', '_repository')
    list_filter = ('preprint__repository__short_name', 'account', 'preprint')
    raw_id_fields = ('preprint', 'account')
    search_fields = ('preprint__pk', 'preprint__title',
                     'account__email', 'account__orcid',
                     'account__first_name', 'account__last_name')


class PreprintVersionAdmin(admin_utils.PreprintFKModelAdmin):
    list_display = ('pk', '_preprint', 'title', 'version', 'date_time',
                    '_repository')
    list_filter = ('preprint__repository__short_name',)
    raw_id_fields = ('preprint', 'file')
    date_hierarchy = ('date_time')
    search_fields = ('preprint__title', 'title', 'abstract',
                     'file__original_filename', 'published_doi')


class CommentAdmin(admin_utils.PreprintFKModelAdmin):
    list_display = ('_body', '_preprint', 'author', '_repository',
                    'date_time', 'is_reviewed', 'is_public')
    list_filter = ('preprint__repository__short_name',
                   'date_time', 'is_reviewed', 'is_public')
    search_fields = ('body', 'preprint__title', 'author__email',
                     'author__first_name', 'author__last_name',)
    raw_id_fields = ('preprint', 'author', 'reply_to',)
    date_hierarchy = ('date_time')

    inlines = [
        admin_utils.CommentInline,
    ]

    def _body(self, obj):
        return truncatewords_html(obj.body, 8) if obj else ''


class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'repository', 'enabled', 'parent')
    list_filter = ('repository__short_name', 'enabled')
    search_fields = ('name', 'slug')
    raw_id_fields = ('editors',)


class VersionQueueAdmin(admin.ModelAdmin):
    list_display = ('pk', 'preprint', 'file', 'update_type',
                    'date_submitted', 'approved', 'date_decision')
    list_filter = ('preprint__repository__short_name', 'update_type',
                   'approved', 'date_submitted', 'date_decision')
    raw_id_fields = ('preprint', 'file',)
    search_fields = ('preprint__title', 'file__original_filename',
                     'title', 'abstract', 'published_doi')
    date_hierarchy = ('date_submitted')


class ReviewAdmin(admin_utils.PreprintFKModelAdmin):
    list_display = ('pk', 'reviewer', '_preprint', 'manager', '_repository',
                    'date_assigned')
    list_display_links = ('pk', 'reviewer')
    list_filter = ('preprint__repository__short_name', 'status',
                   'anonymous', 'notification_sent', 'date_assigned',
                   'date_accepted', 'date_due', 'date_completed')
    raw_id_fields = ('preprint', 'manager', 'reviewer', 'comment')
    search_fields = ('preprint__pk', 'preprint__title',
                     'reviewer__email', 'reviewer__first_name',
                     'reviewer__last_name', 'manager__email',
                     'manager__first_name', 'manager__last_name')
    date_hierarchy = ('date_assigned')


class ReviewRecommendationAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'repository')
    list_display_links = ('pk', 'name',)
    list_filter = ('repository',)
    raw_id_fields = ('repository',)
    search_fields = ('name',)


admin_list = [
    (models.Repository, RepositoryAdmin),
    (models.RepositoryRole, RepositoryRoleAdmin),
    (models.RepositoryField, RepositoryFieldAdmin),
    (models.RepositoryFieldAnswer, RepositoryFieldAnswerAdmin),
    (models.Preprint, PreprintAdmin),
    (models.KeywordPreprint, KeywordPreprintAdmin),
    (models.PreprintFile, PreprintFileAdmin),
    (models.PreprintSupplementaryFile, PreprintSupplementaryFileAdmin),
    (models.PreprintAccess, PreprintAccessAdmin),
    (models.PreprintAuthor, PreprintAuthorAdmin),
    (models.PreprintVersion, PreprintVersionAdmin),
    (models.Comment, CommentAdmin),
    (models.Subject, SubjectAdmin),
    (models.VersionQueue, VersionQueueAdmin),
    (models.Review, ReviewAdmin),
    (models.ReviewRecommendation, ReviewRecommendationAdmin),
]

[admin.site.register(*t) for t in admin_list]
