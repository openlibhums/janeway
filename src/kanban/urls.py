__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
from django.conf.urls import url

from kanban import views

urlpatterns = [
    #url(r'^$', views.home, name='kanban_home'),
    #url(r'^article/(?P<article_id>\d+)/note/new/$', views.new_note, name='kanban_new_note'),
    url(r'^article/(?P<article_id>\d+)/file/(?P<file_id>\d+)/$', views.serve_article_file, name='serve_article_file'),
]
