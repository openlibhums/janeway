__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
from django.conf.urls import url

from proofing import views

urlpatterns = [
    # PM
    url(r'^$', views.proofing_list, name='proofing_list'),
    url(r'^(?P<article_id>\d+)/assign_manager/(?P<user_id>\d+)/$', views.proofing_assign_article,
        name='proofing_assign_article_with_user'),
    url(r'^(?P<article_id>\d+)/$', views.proofing_article, name='proofing_article'),
    url(r'^unassign/(?P<article_id>\d+)/$', views.proofing_unassign_article, name='proofing_unassign_article'),
    url(r'^(?P<article_id>\d+)/proofing_task/(?P<proofing_task_id>\d+)/notify/$', views.notify_proofreader,
        name='notify_proofreader'),
    url(r'^(?P<article_id>\d+)/proofing_task/(?P<proofing_task_id>\d+)/edit/$', views.edit_proofing_assignment,
        name='edit_proofing_assignment'),

    url(r'^(?P<article_id>\d+)/round/(?P<round_id>\d+)/edit/$',
        views.delete_proofing_round,
        name='delete_proofing_round'),

    url(r'^(?P<article_id>\d+)/proofing_task/(?P<proofing_task_id>\d+)/review/$', views.do_proofing,
        name='review_proofing_task'),
    url(r'^(?P<article_id>\d+)/proofing_task/(?P<proofing_task_id>\d+)/corrections/$',
        views.request_typesetting_changes,
        name='request_typesetting_changes'),
    url(r'^(?P<article_id>\d+)/proofing_task/(?P<proofing_task_id>\d+)/corrections/(?P<typeset_task_id>\d+)/notify/$',
        views.notify_typesetter_changes,
        name='notify_typesetter_changes'),
    url(r'^(?P<article_id>\d+)/ack/(?P<model_name>proofing|correction)/id/(?P<model_pk>\d+)/$',
        views.acknowledge,
        name='acknowledge_proofing'),
    url(r'^(?P<article_id>\d+)/complete/$', views.complete_proofing, name='complete_proofing'),

    # Proofreader
    url(r'^requests/$', views.proofing_requests, name='proofing_requests'),
    url(r'^requests/(?P<proofing_task_id>\d+)/$', views.do_proofing, name='do_proofing'),
    url(r'^requests/(?P<proofing_task_id>\d+)/decision/(?P<decision>accept|decline)/$',
        views.proofing_requests,
        name='proofing_requests_decision'),
    url(r'^requests/(?P<proofing_task_id>\d+)/file/(?P<file_id>\d+)/download/$', views.proofing_download,
        name='proofing_download'),
    url(r'^requests/(?P<proofing_task_id>\d+)/file/(?P<file_id>\d+)/download/galley.epub$', views.proofing_download,
        name='proofing_epub_download'),
    url(r'^requests/(?P<proofing_task_id>\d+)/preview/(?P<galley_id>\d+)/$', views.preview_galley,
        name='preview_galley'),
    url(r'^requests/(?P<proofing_task_id>\d+)/galley/(?P<galley_id>\d+)/new_note/$',
        views.new_note,
        name='proofing_new_note'),
    url(r'^requests/(?P<proofing_task_id>\d+)/galley/(?P<galley_id>\d+)/delete/$',
        views.delete_note,
        name='proofing_delete_note'),

    url(r'^requests/(?P<proofing_task_id>\d+)/preview/(?P<galley_id>\d+)/(?P<file_name>.*)$', views.preview_figure,
        name='preview_figure'),

    # Corrections
    url(r'^requests/corrections/(?P<typeset_task_id>\d+)/decision/(?P<decision>accept|decline)/$',
        views.proofing_requests,
        name='proofing_requests_decision_typesetting'),
    url(r'^requests/corrections/(?P<typeset_task_id>\d+)/$',
        views.typesetting_corrections,
        name='typesetting_corrections'),
]
