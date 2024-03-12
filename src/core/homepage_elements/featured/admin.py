from django.contrib import admin

from core.homepage_elements.featured import models


class FeaturedArticleAdmin(admin.ModelAdmin):
    list_display = ('article', 'sequence', 'journal', 'added', 'added_by')
    list_filter = ('journal', 'added')
    search_fields = ('article__pk', 'article__title')
    raw_id_fields = ('article', 'added_by')
    date_hierarchy = ('added')


admin_list = [
    (models.FeaturedArticle, FeaturedArticleAdmin),
]

[admin.site.register(*t) for t in admin_list]
