__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
import csv

from django.contrib import admin
from django.http import HttpResponse

from utils import admin_utils
from metrics import models
from submission import models as submission_models


def _export_as_csv(self, request, queryset):
    meta = self.model._meta
    field_names = [field.name for field in meta.fields]

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename={}.csv'.format(meta)
    writer = csv.writer(response)

    writer.writerow(field_names)
    for obj in queryset:
        writer.writerow([getattr(obj, field) for field in field_names])

    return response


class ArticleAccessAdmin(admin_utils.ArticleFKModelAdmin):
    """Displays objects in the Django admin interface."""
    list_display = ('_article', 'accessed', 'country',
                    'type', 'galley_type', '_journal')
    list_filter = ('article__journal', 'accessed', 'type', 'galley_type',)
    search_fields = ('article__title', 'article__pk', 'identifier',
                     'article__journal__code',
                     'type', 'galley_type', 'accessed', 'country__code',
                     'country__name')
    raw_id_fields = ('article',)
    date_hierarchy = ('accessed')

    def get_form(self, request, obj=None, **kwargs):
        form = super(ArticleAccessAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['article'].queryset = submission_models.Article.objects.all()
        return form


class HistoricArticleAccessAdmin(admin_utils.ArticleFKModelAdmin):
    list_display = ('_article', 'views', 'downloads', '_journal')
    list_filter = ('article__journal',)
    raw_id_fields = ('article',)


class AltMetricAdmin(admin_utils.ArticleFKModelAdmin):
    list_display = ('_article', 'source', 'pid', '_journal')
    list_filter = ('article__journal', 'source', 'timestamp')
    search_fields = ('article__title', 'article__pk', 'source',
                     'pid')
    date_hierarchy = ('timestamp')
    raw_id_fields = ('article',)


class ArticleLinkAdmin(admin_utils.ArticleFKModelAdmin):
    list_display = ('pk', 'object_type', 'doi', 'year', '_article',
                    '_journal')
    list_filter = ('article__journal', 'object_type', 'year',)
    search_fields = ('article__title', 'article__pk', 'doi', 'year',
                     'article_title', 'journal_title', 'journal_issn')

    actions = ["export_as_csv"]

    def export_as_csv(self, request, queryset):
        return _export_as_csv(self, request, queryset)

    export_as_csv.short_description = "Export Selected"


class BookLinkAdmin(admin_utils.ArticleFKModelAdmin):
    list_display = ('pk', 'object_type', 'doi', 'year', '_article',
                    '_journal')
    list_filter = ('article__journal', 'object_type', 'year',)
    search_fields = ('article__title', 'article__pk', 'doi', 'year',
                     'title', 'isbn_print', 'isbn_electronic')

    actions = ["export_as_csv"]

    def export_as_csv(self, request, queryset):
        return _export_as_csv(self, request, queryset)

    export_as_csv.short_description = "Export Selected"


admin_list = [
    (models.AltMetric, AltMetricAdmin),
    (models.ArticleAccess, ArticleAccessAdmin),
    (models.HistoricArticleAccess, HistoricArticleAccessAdmin),
    (models.ArticleLink, ArticleLinkAdmin),
    (models.BookLink, BookLinkAdmin),
]

[admin.site.register(*t) for t in admin_list]
