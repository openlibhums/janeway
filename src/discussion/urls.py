__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve, Andy Byers & Mauro Sanchez"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
from django.urls import re_path

from discussion import views

urlpatterns = [
    re_path(r'^(?P<object_type>preprint|article)/(?P<object_id>\d+)/$', views.threads, name='discussion_threads'),
    re_path(r'^(?P<object_type>preprint|article)/(?P<object_id>\d+)/thread/(?P<thread_id>\d+)/$', views.threads, name='discussion_thread'),
    re_path(r'^thread/(?P<thread_id>\d+)/post/new/$', views.add_post, name='discussion_add_post'),
]
