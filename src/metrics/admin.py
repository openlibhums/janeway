__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.contrib import admin

from metrics import models
from submission import models as submission_models


class ArticleAccessAdmin(admin.ModelAdmin):
    """Displays objects in the Django admin interface."""
    list_display = ('article', 'type', 'identifier', 'accessed')
    list_filter = ('type', 'galley_type')
    search_fields = ('identifier',)
    raw_id_fields = ('article',)

    def get_form(self, request, obj=None, **kwargs):
        form = super(ArticleAccessAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['article'].queryset = submission_models.Article.allarticles.all()
        return form


class HistoricArticleAccessAdmin(admin.ModelAdmin):
    list_display = ('article', 'views', 'downloads')
    raw_id_fields = ('article',)


class AltMetricAdmin(admin.ModelAdmin):
    list_display = ('article', 'source', 'pid')
    list_filter = ('article', 'source')
    raw_id_fields = ('article',)


class ForwardLinkAdmin(admin.ModelAdmin):
    list_display = ('pk', 'article', 'object_type', 'doi', 'year')
    list_filter = ('object_type', 'year',)
    search_fields = ('article__title', 'doi',)


admin_list = [
    (models.AltMetric, AltMetricAdmin),
    (models.ArticleAccess, ArticleAccessAdmin),
    (models.HistoricArticleAccess, HistoricArticleAccessAdmin),
    (models.ForwardLink, ForwardLinkAdmin),
    (models.ArticleLink,),
    (models.BookLink,),
]

[admin.site.register(*t) for t in admin_list]
