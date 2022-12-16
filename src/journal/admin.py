__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.contrib import admin

from journal import models
from utils import admin_utils


class IssueAdmin(admin.ModelAdmin):
    list_display = ('pk', 'issue_title', 'volume', 'issue', 'date',
                    'journal', 'issue_type')
    list_display_links = ('pk', 'issue_title')
    list_filter = ('journal', 'date')
    search_fields = ('pk', 'issue_title', 'volume', 'issue',
                     'journal__code')
    date_hierarchy = ('date')
    filter_horizontal = ('articles',)
    raw_id_fields = ('issue_type',)

    inlines = [
        admin_utils.IssueGalleyInline,
        admin_utils.SectionOrderingInline,
        admin_utils.ArticleOrderingInline,
    ]


class IssueTypeAdmin(admin.ModelAdmin):
    list_display = ('code', 'pretty_name', 'journal')
    list_filter = ('journal',)
    search_fields = ('code', 'pretty_name')


class IssueGalleyAdmin(admin.ModelAdmin):
    list_display = ('pk', 'file', 'issue', 'journal')
    list_display_links = ('pk', 'file')
    list_filter = ('issue__journal',)
    search_fields = ('pk', 'file__original_filename', 'issue__journal__code',
                     'issue__issue_title', 'issue__volume', 'issue__issue')

    def journal(self, obj):
        return obj.issue.journal if obj else ''


class IssueEditorAdmin(admin.ModelAdmin):
    list_display = ('account', 'issue', 'journal', 'role')
    list_filter = ('issue__journal', 'role',)
    search_fields = ('account__email', 'account__first_name',
                     'account__last_name', 'role', 'issue__issue_title',
                     'issue__journal__code')

    raw_id_fields = ('account', 'issue')

    def journal(self, obj):
        return obj.issue.journal if obj else ''


class JournalAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'code',
        'domain',
        'is_remote',
        'is_conference',
        'hide_from_press',
    )
    list_filter = ('is_remote', 'is_conference', 'hide_from_press')
    raw_id_fields = (
        'carousel',
        'current_issue',
        'thumbnail_image',
        'xsl',
    )
    filter_horizontal = ('keywords',)


class PinnedArticleAdmin(admin.ModelAdmin):
    list_display = ('article', 'journal', 'sequence')
    list_filter = ('journal',)
    search_fields = ('journal__code', 'article__title')
    raw_id_fields = ('article',)


class BannedIPAdmin(admin.ModelAdmin):
    list_display = ('ip', 'date_banned')
    list_filter = ('date_banned',)
    search_fields = ('ip', )
    date_hierarchy = ('date_banned')


class NotificationsAdmin(admin.ModelAdmin):
    list_display = ('journal', 'user', 'domain', 'type', 'active')
    list_filter = ('journal', 'domain', 'type', 'active')
    search_fields = ('journal__code', 'user__email',
                     'user__first_name', 'user__last_name',
                     'domain', 'type')
    raw_id_fields = ('user',)


class ArticleOrderingAdmin(admin.ModelAdmin):
    list_display = ('order', 'article', 'issue', 'journal', 'section')
    list_filter = ('article__journal',)
    search_fields = ('article__title', 'section__name', 'issue__issue_title',
                     'issue__journal__code', 'issue__volume', 'issue__issue')
    raw_id_fields = ('article',)

    def journal(self, obj):
        return obj.article.journal.code if obj else ''


class FixedPubCheckItemsAdmin(admin.ModelAdmin):
    list_display = ('article', 'journal', 'metadata', 'verify_doi',
                    'select_issue', 'set_pub_date', 'notify_the_author',
                    'select_render_galley', 'select_article_image',
                    'select_open_reviews')
    list_filter = ('article__journal', 'metadata', 'verify_doi',
                   'select_issue', 'set_pub_date', 'notify_the_author',
                   'select_render_galley', 'select_article_image',
                   'select_open_reviews')
    search_fields = ('article__pk', 'article__title', 'article__journal__code')
    raw_id_fields = ('article',)

    def journal(self, obj):
        return obj.article.journal if obj else ''


class PresetPublicationCheckItemAdmin(admin.ModelAdmin):
    list_display = ('journal', 'title', 'enabled')
    list_filter = ('journal', 'enabled')
    search_fields = ('journal__code', 'title', 'text')


class PrePublicationChecklistItemAdmin(admin.ModelAdmin):
    list_display = ('article', 'journal', 'completed', 'completed_by',
                    'completed_on')
    list_filter = ('article__journal', 'completed', 'completed_on')
    search_fields = ('article__title', 'article__journal__code',
                     'completed_by__email', 'completed_by__first_name',
                     'completed_by__last_name')
    date_hierarchy = ('completed_on')
    raw_id_fields = (
        'completed_by',
        'article',
    )

    def journal(self, obj):
        return obj.article.journal if obj else ''


class SectionOrderingAdmin(admin.ModelAdmin):
    list_display = ('pk', 'section', 'issue', 'journal', 'order')
    list_display_links = ('section',)
    search_fields = ('section__name', 'issue__issue_title',
                     'issue__journal__code', 'issue__volume', 'issue__issue')

    def journal(self, obj):
        return obj.issue.journal if obj else ''


admin_list = [
    (models.Issue, IssueAdmin),
    (models.IssueType, IssueTypeAdmin),
    (models.IssueGalley, IssueGalleyAdmin),
    (models.IssueEditor, IssueEditorAdmin),
    (models.Journal, JournalAdmin),
    (models.PinnedArticle, PinnedArticleAdmin),
    (models.PresetPublicationCheckItem, PresetPublicationCheckItemAdmin),
    (models.PrePublicationChecklistItem, PrePublicationChecklistItemAdmin),
    (models.FixedPubCheckItems, FixedPubCheckItemsAdmin),
    (models.ArticleOrdering, ArticleOrderingAdmin),
    (models.SectionOrdering, SectionOrderingAdmin),
    (models.BannedIPs, BannedIPAdmin),
    (models.Notifications, NotificationsAdmin),
]

[admin.site.register(*t) for t in admin_list]
