__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django.urls import re_path

from copyediting import views


urlpatterns = [

    # Editor URLs
    re_path(r'^$', views.copyediting, name='copyediting'),
    re_path(r'^article/(?P<article_id>\d+)/$', views.article_copyediting, name='article_copyediting'),
    re_path(r'^article/(?P<article_id>\d+)/assignment/add/$', views.add_copyeditor_assignment,
        name='add_copyeditor_assignment'),
    re_path(r'^article/(?P<article_id>\d+)/assignment/(?P<copyedit_id>\d+)/$', views.notify_copyeditor_assignment,
        name='notify_copyeditor_assignment'),
    re_path(r'^article/(?P<article_id>\d+)/assignment/(?P<copyedit_id>\d+)/edit/$', views.edit_assignment,
        name='copyedit_edit_assignment'),
    re_path(r'^article/(?P<article_id>\d+)/assignment/(?P<copyedit_id>\d+)/review/$', views.editor_review,
        name='editor_review'),
    re_path(r'^article/(?P<article_id>\d+)/assignment/(?P<copyedit_id>\d+)/author_review/(?P<author_review_id>\d+)/$', views.request_author_copyedit,
        name='request_author_copyedit'),
    re_path(r'^article/(?P<article_id>\d+)/assignment/(?P<copyedit_id>\d+)/author_review/(?P<author_review_id>\d+)/delete/$', views.delete_author_review,
        name='delete_author_review'),

    # Author URLs
    re_path(r'^author/article/(?P<article_id>\d+)/assignment/(?P<author_review_id>\d+)/$', views.author_copyedit,
        name='author_copyedit'),
    re_path(r'^author/article/(?P<article_id>\d+)/assignment/(?P<author_review_id>\d+)/file/(?P<file_id>\d+)/update/$',
        views.author_update_file, name='author_update_file'),

    # Copyeditor URLs
    re_path(r'^requests/$', views.copyedit_requests, name='copyedit_requests'),
    re_path(r'^requests/(?P<copyedit_id>\d+)/$', views.do_copyedit, name='do_copyedit'),
    re_path(r'^requests/(?P<copyedit_id>\d+)/files/upload/$', views.do_copyedit_add_file, name='do_copyedit_add_file'),
    re_path(r'^requests/(?P<copyedit_id>\d+)/files/(?P<file_id>\d+)/download/$', views.copyeditor_file,
        name='copyeditor_file'),
    re_path(r'^requests/(?P<copyedit_id>\d+)/(?P<decision>accept|decline)/$', views.copyedit_request_decision,
        name='copyedit_request_decision'),

]
