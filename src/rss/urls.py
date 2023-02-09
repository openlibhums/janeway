__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
from django.conf.urls import url
from rss import views

urlpatterns = [
    url(r'^news/$', views.LatestNewsFeed(), name='rss_news'),
    url(r'^articles/$', views.LatestArticlesFeed(), name='rss_articles'),
    url(r'^preprints/$', views.LatestPreprintsFeed(), name='rss_preprints'),
    url(r'^', views.LatestArticlesFeed(), name='rss_articles'),
]
