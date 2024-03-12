from django.urls import re_path
from core.homepage_elements.news import views

urlpatterns = [
    # Featured Articles
    re_path(r'^$', views.news_config, name='news_config'),
]
