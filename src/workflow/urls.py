__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve, Andy Byers & Mauro Sanchez"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django.conf.urls import url

from workflow import views


urlpatterns = [
    url(r'^article/(?P<article_id>\d+)/$',
        views.manage_article_workflow,
        name='manage_article_workflow'),
    url(r'^article/(?P<article_id>\d+)/move_to_next/$',
        views.move_to_next_workflow_element,
        name='move_to_next_workflow_element'),
]
