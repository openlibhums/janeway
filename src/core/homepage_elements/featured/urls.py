from django.urls import re_path
from core.homepage_elements.featured import views

urlpatterns = [
    # Featured Articles
    re_path(r'^manager/$', views.featured_articles, name='featured_articles_setup'),
    re_path(r'^manager/order/$', views.featured_articles_order, name='featured_order'),
]
