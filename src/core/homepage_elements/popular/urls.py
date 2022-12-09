from django.urls import re_path
from core.homepage_elements.popular import views

urlpatterns = [
    # Featured Articles
    re_path(r'^manager/$', views.featured_articles, name='popular_articles_setup'),
]
