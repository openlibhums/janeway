__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django.urls import re_path

from cms import views

urlpatterns = [
    # Probably needs some multi-journal logic here
    re_path(r'^$', views.index, name='cms_index'),
    re_path(r'^page/new/$', views.page_manage, name='cms_page_new'),
    re_path(r'^page/(?P<page_id>\d+)/$', views.page_manage, name='cms_page_edit'),
    re_path(r'^(?P<page_name>w+?)$', views.view_page, name='cms_page'),

    re_path(r'^nav/$', views.nav, name='cms_nav'),
    re_path(r'^nav/(?P<nav_id>\d+)/$', views.nav, name='cms_nav_edit'),

    re_path(r'^submission_items/$', views.submission_items, name='cms_submission_items'),
    re_path(r'^submission_items/add/$',
        views.order_submission_items,
        name='cms_order_submission_items',
        ),
    re_path(r'^submission_items/order/$',
        views.edit_or_create_submission_item,
        name='cms_add_submission_item',
        ),
    re_path(r'^submission_items/(?P<item_id>\d+)/$',
        views.edit_or_create_submission_item,
        name='cms_edit_submission_item',
        ),
    re_path(r'^media_files/$',
        views.file_list,
        name='cms_file_list',
        ),
    re_path(r'^media_files/upload/$',
        views.file_upload,
        name='cms_file_upload',
        ),
]
