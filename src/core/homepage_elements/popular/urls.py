from django.conf.urls import url
from core.homepage_elements.popular import views

urlpatterns = [
    # Featured Articles
    url(r'^manager/$', views.featured_articles, name='popular_articles_setup'),
]
