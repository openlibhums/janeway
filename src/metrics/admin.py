__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
import csv

from django.contrib import admin
from django.http import HttpResponse

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


class ArticleAccessAdmin(admin.ModelAdmin):
    """Displays objects in the Django admin interface."""
    list_display = ('article', 'type', 'identifier', 'accessed')
    list_filter = ('type', 'galley_type', 'article')
    search_fields = ('identifier',)
    raw_id_fields = ('article',)

    def get_form(self, request, obj=None, **kwargs):
        form = super(ArticleAccessAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['article'].queryset = submission_models.Article.objects.all()
        return form


class HistoricArticleAccessAdmin(admin.ModelAdmin):
    list_display = ('article', 'views', 'downloads')
    raw_id_fields = ('article',)


class AltMetricAdmin(admin.ModelAdmin):
    list_display = ('article', 'source', 'pid')
    list_filter = ('article', 'source')
    raw_id_fields = ('article',)


class ArticleLinkAdmin(admin.ModelAdmin):
    list_display = ('pk', 'article', 'object_type', 'doi', 'year')
    list_filter = ('object_type', 'year',)
    search_fields = ('article__title', 'doi',)

    actions = ["export_as_csv"]

    def export_as_csv(self, request, queryset):
        return _export_as_csv(self, request, queryset)

    export_as_csv.short_description = "Export Selected"


class BookLinkAdmin(admin.ModelAdmin):
    list_display = ('pk', 'article', 'object_type', 'doi', 'year')
    list_filter = ('object_type', 'year',)
    search_fields = ('article__title', 'doi',)

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
