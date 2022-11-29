__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.contrib import admin
from django.contrib.contenttypes.models import ContentType

from utils import models
from journal import models as journal_models
from submission import models as submission_models
from repository import models as repository_models


class GenericRelationArticleJournalFilter(admin.SimpleListFilter):
    """
    Provides a journal list filter for objects that are separated from the
    journal by a Generic Foreign Key and an article-journal relationship.
    An example is utils.LogEntry.
    This and similar classes are implemented here in utils.admin
    to avoid circular imports.
    """

    title = 'journal'
    parameter_name = 'journal'

    def lookups(self, request, model_admin):
        return (
            (journal.id, journal.code)
            for journal in journal_models.Journal.objects.all()
        )

    def queryset(self, request, queryset):
        journal_pk = request.GET.get('journal', None)
        if not journal_pk:
            return queryset
        articles = submission_models.Article.objects.filter(
            journal__id=journal_pk
        )
        if not articles:
            return queryset.none()
        content_type = ContentType.objects.get_for_model(articles.first())
        return queryset.filter(
            object_id__in=[article.pk for article in articles],
            content_type=content_type,
        )


class GenericRelationPreprintRepositoryFilter(admin.SimpleListFilter):
    """
    Provides a repository list filter for objects that are separated from the
    repository by a Generic Foreign Key and an preprint-repository relationship.
    An example is utils.LogEntry.
    """

    title = 'repository'
    parameter_name = 'repository'

    def lookups(self, request, model_admin):
        return (
            (repository.id, repository.short_name)
            for repository in repository_models.Repository.objects.all()
        )

    def queryset(self, request, queryset):
        repo_pk = request.GET.get('repository', None)
        if not repo_pk:
            return queryset
        preprints = repository_models.Preprint.objects.filter(
           repository__id=repo_pk
        )
        if not preprints:
            return queryset.none()
        content_type = ContentType.objects.get_for_model(preprints.first())
        return queryset.filter(
            object_id__in=[preprint.pk for preprint in preprints],
            content_type=content_type,
        )


class ImportCacheAdmin(admin.ModelAdmin):
    list_display = ('url', 'mime_type', 'date_time')
    list_filter = ('url', 'mime_type')


class PluginAdmin(admin.ModelAdmin):
    list_display = ('name', 'version', 'date_installed', 'enabled', 'display_name', 'press_wide')


class LogAdmin(admin.ModelAdmin):
    list_display = ('pk', 'types', 'date', 'level', 'actor', 'ip_address',
                    'is_email', 'email_subject', 'content_type', 'target')
    list_filter = (GenericRelationArticleJournalFilter,
                   GenericRelationPreprintRepositoryFilter,
                   'date', 'is_email', 'types')
    search_fields = ('types', 'email_subject', 'actor__email',
                     'actor__first_name', 'actor__last_name',
                     'ip_address', 'email_subject')
    date_hierarchy = ('date')
    raw_id_fields = ('actor',)



class VersionAdmin(admin.ModelAdmin):
    list_display = ('number', 'date', 'rollback')


admin_list = [
    (models.LogEntry, LogAdmin),
    (models.Plugin, PluginAdmin),
    (models.ImportCacheEntry, ImportCacheAdmin),
    (models.Version, VersionAdmin)
]

[admin.site.register(*t) for t in admin_list]
