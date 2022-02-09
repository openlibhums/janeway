__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve, Andy Byers & Mauro Sanchez"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
from django.conf.urls import url

from discussion import views

urlpatterns = [
    url(r'^(?P<object_type>preprint|article)/(?P<object_id>\d+)/$', views.threads, name='discussion_threads'),
    url(r'^(?P<object_type>preprint|article)/(?P<object_id>\d+)/thread/(?P<thread_id>\d+)/$', views.threads, name='discussion_thread'),
    url(r'^thread/(?P<thread_id>\d+)/post/new/$', views.add_post, name='discussion_add_post'),
]
