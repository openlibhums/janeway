__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django.conf.urls import url

from copyediting import views


urlpatterns = [

    # Editor URLs
    url(r'^$', views.copyediting, name='copyediting'),
    url(r'^article/(?P<article_id>\d+)/$', views.article_copyediting, name='article_copyediting'),
    url(r'^article/(?P<article_id>\d+)/assignment/add/$', views.add_copyeditor_assignment,
        name='add_copyeditor_assignment'),
    url(r'^article/(?P<article_id>\d+)/assignment/(?P<copyedit_id>\d+)/$', views.notify_copyeditor_assignment,
        name='notify_copyeditor_assignment'),
    url(r'^article/(?P<article_id>\d+)/assignment/(?P<copyedit_id>\d+)/edit/$', views.edit_assignment,
        name='copyedit_edit_assignment'),
    url(r'^article/(?P<article_id>\d+)/assignment/(?P<copyedit_id>\d+)/review/$', views.editor_review,
        name='editor_review'),
    url(r'^article/(?P<article_id>\d+)/assignment/(?P<copyedit_id>\d+)/author_review/(?P<author_review_id>\d+)/$', views.request_author_copyedit,
        name='request_author_copyedit'),
    url(r'^article/(?P<article_id>\d+)/assignment/(?P<copyedit_id>\d+)/author_review/(?P<author_review_id>\d+)/delete/$', views.delete_author_review,
        name='delete_author_review'),

    # Author URLs
    url(r'^author/article/(?P<article_id>\d+)/assignment/(?P<author_review_id>\d+)/$', views.author_copyedit,
        name='author_copyedit'),
    url(r'^author/article/(?P<article_id>\d+)/assignment/(?P<author_review_id>\d+)/file/(?P<file_id>\d+)/update/$',
        views.author_update_file, name='author_update_file'),

    # Copyeditor URLs
    url(r'^requests/$', views.copyedit_requests, name='copyedit_requests'),
    url(r'^requests/(?P<copyedit_id>\d+)/$', views.do_copyedit, name='do_copyedit'),
    url(r'^requests/(?P<copyedit_id>\d+)/files/upload/$', views.do_copyedit_add_file, name='do_copyedit_add_file'),
    url(r'^requests/(?P<copyedit_id>\d+)/files/(?P<file_id>\d+)/download/$', views.copyeditor_file,
        name='copyeditor_file'),
    url(r'^requests/(?P<copyedit_id>\d+)/(?P<decision>accept|decline)/$', views.copyedit_request_decision,
        name='copyedit_request_decision'),

]
