from django.contrib import admin

from core.homepage_elements.featured import models

admin_list = [
    (models.FeaturedArticle, ),
]

[admin.site.register(*t) for t in admin_list]
