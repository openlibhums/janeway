__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve, Andy Byers & Mauro Sanchez"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.urls import re_path

from workflow import views


urlpatterns = [
    re_path(r'^article/(?P<article_id>\d+)/$',
        views.manage_article_workflow,
        name='manage_article_workflow'),
    re_path(r'^article/(?P<article_id>\d+)/move_to_next/$',
        views.move_to_next_workflow_element,
        name='move_to_next_workflow_element'),
]
