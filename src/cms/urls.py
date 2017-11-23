__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django.conf.urls import url

from cms import views

urlpatterns = [
    # Probably needs some multi-journal logic here
    url(r'^$', views.index, name='cms_index'),
    url(r'^page/new/$', views.page_manage, name='cms_page_new'),
    url(r'^page/(?P<page_id>\d+)/$', views.page_manage, name='cms_page_edit'),
    url(r'^(?P<page_name>w+?)$', views.view_page, name='cms_page'),

    url(r'^nav/$', views.nav, name='cms_nav'),
    url(r'^nav/(?P<nav_id>\d+)/$', views.nav, name='cms_nav_edit'),
]
