from django.contrib import admin

from core.homepage_elements.featured.models import *

admin_list = [
    (FeaturedArticle, ),
]

[admin.site.register(*t) for t in admin_list]
