__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.contrib import admin

from journal import models


class IssueAdmin(admin.ModelAdmin):
    list_display = ('volume', 'issue', 'issue_title', 'journal', 'issue_type')
    list_filter = ('journal', 'issue_type')
    search_fields = ('issue_title',)
    filter_horizontal = ('articles',)


class IssueTypeAdmin(admin.ModelAdmin):
    list_filter = ('journal',)
    search_fields = ('pretty_name', 'code')


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
        'current_issue',
        'thumbnail_image',
        'press_image_override',
    )
    filter_horizontal = ('keywords',)


class BannedIPAdmin(admin.ModelAdmin):
    list_display = ('ip', 'date_banned')


class NotificationsAdmin(admin.ModelAdmin):
    pass


class ArticleOrderingAdmin(admin.ModelAdmin):
    list_display = ('article', 'issue', 'section', 'order')
    list_filter = ('issue', 'section')
    search_fields = ('article__title',)


admin_list = [
    (models.Issue, IssueAdmin),
    (models.IssueType, IssueTypeAdmin),
    (models.Journal, JournalAdmin),
    (models.PresetPublicationCheckItem,),
    (models.PrePublicationChecklistItem,),
    (models.FixedPubCheckItems,),
    (models.ArticleOrdering, ArticleOrderingAdmin),
    (models.SectionOrdering,),
    (models.BannedIPs, BannedIPAdmin),
    (models.Notifications,),
]

[admin.site.register(*t) for t in admin_list]
