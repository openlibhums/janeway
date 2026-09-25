__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
from django.urls import path
from django.urls import re_path
from rss import views

urlpatterns = [
    path("news/", views.LatestNewsFeed(), name="rss_news"),
    path("articles/", views.LatestArticlesFeed(), name="rss_articles"),
    path("preprints/", views.LatestPreprintsFeed(), name="rss_preprints"),
    re_path(r"^", views.LatestArticlesFeed(), name="rss_articles"),
]
