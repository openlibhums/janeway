__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.contrib import admin

from journal import models


class IssueAdmin(admin.ModelAdmin):
    """Displays Setting objects in the Django admin interface."""
    list_display = ('volume', 'issue', 'issue_title', 'journal', 'issue_type')
    list_filter = ('journal', 'issue_type')
    search_fields = ('issue_title',)


class JournalAdmin(admin.ModelAdmin):
    """Displays Setting objects in the Django admin interface."""
    list_display = ('name', 'code', 'domain', 'is_remote', 'hide_from_press')
    list_filter = ('is_remote', 'hide_from_press')


admin_list = [
    (models.Issue, IssueAdmin),
    (models.Journal, JournalAdmin),
    (models.PresetPublicationCheckItem,),
    (models.PrePublicationChecklistItem,),
    (models.FixedPubCheckItems,),
    (models.ArticleOrdering,),
    (models.SectionOrdering,)
]

[admin.site.register(*t) for t in admin_list]
