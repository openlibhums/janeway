from django.conf.urls import url
from core.homepage_elements.news import views

urlpatterns = [
    # Featured Articles
    url(r'^$', views.news_config, name='news_config'),
]
