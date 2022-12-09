__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
from django.urls import re_path

from proofing import views

urlpatterns = [
    # PM
    re_path(r'^$', views.proofing_list, name='proofing_list'),
    re_path(r'^(?P<article_id>\d+)/assign_manager/(?P<user_id>\d+)/$', views.proofing_assign_article,
        name='proofing_assign_article_with_user'),
    re_path(r'^(?P<article_id>\d+)/$', views.proofing_article, name='proofing_article'),
    re_path(r'^unassign/(?P<article_id>\d+)/$', views.proofing_unassign_article, name='proofing_unassign_article'),
    re_path(r'^(?P<article_id>\d+)/proofing_task/(?P<proofing_task_id>\d+)/notify/$', views.notify_proofreader,
        name='notify_proofreader'),
    re_path(r'^(?P<article_id>\d+)/proofing_task/(?P<proofing_task_id>\d+)/edit/$', views.edit_proofing_assignment,
        name='edit_proofing_assignment'),

    re_path(r'^(?P<article_id>\d+)/round/(?P<round_id>\d+)/edit/$',
        views.delete_proofing_round,
        name='delete_proofing_round'),

    re_path(r'^(?P<article_id>\d+)/proofing_task/(?P<proofing_task_id>\d+)/review/$', views.do_proofing,
        name='review_proofing_task'),
    re_path(r'^(?P<article_id>\d+)/proofing_task/(?P<proofing_task_id>\d+)/corrections/$',
        views.request_typesetting_changes,
        name='request_typesetting_changes'),
    re_path(r'^(?P<article_id>\d+)/proofing_task/(?P<proofing_task_id>\d+)/corrections/(?P<typeset_task_id>\d+)/notify/$',
        views.notify_typesetter_changes,
        name='notify_typesetter_changes'),
    re_path(r'^(?P<article_id>\d+)/ack/(?P<model_name>proofing|correction)/id/(?P<model_pk>\d+)/$',
        views.acknowledge,
        name='acknowledge_proofing'),
    re_path(r'^(?P<article_id>\d+)/complete/$', views.complete_proofing, name='complete_proofing'),

    # Proofreader
    re_path(r'^requests/$', views.proofing_requests, name='proofing_requests'),
    re_path(r'^requests/(?P<proofing_task_id>\d+)/$', views.do_proofing, name='do_proofing'),
    re_path(r'^requests/(?P<proofing_task_id>\d+)/decision/(?P<decision>accept|decline)/$',
        views.proofing_requests,
        name='proofing_requests_decision'),
    re_path(r'^requests/(?P<proofing_task_id>\d+)/file/(?P<file_id>\d+)/download/$', views.proofing_download,
        name='proofing_download'),
    re_path(r'^requests/(?P<proofing_task_id>\d+)/file/(?P<file_id>\d+)/download/galley.epub$', views.proofing_download,
        name='proofing_epub_download'),
    re_path(r'^requests/(?P<proofing_task_id>\d+)/preview/(?P<galley_id>\d+)/$', views.preview_galley,
        name='preview_galley'),
    re_path(r'^requests/(?P<proofing_task_id>\d+)/galley/(?P<galley_id>\d+)/new_note/$',
        views.new_note,
        name='proofing_new_note'),
    re_path(r'^requests/(?P<proofing_task_id>\d+)/galley/(?P<galley_id>\d+)/delete/$',
        views.delete_note,
        name='proofing_delete_note'),

    re_path(r'^requests/(?P<proofing_task_id>\d+)/preview/(?P<galley_id>\d+)/(?P<file_name>.*)$', views.preview_figure,
        name='preview_figure'),

    # Corrections
    re_path(r'^requests/corrections/$',
        views.correction_requests,
        name='proofing_correction_requests'),
    re_path(r'^requests/corrections/(?P<typeset_task_id>\d+)/$',
        views.typesetting_corrections,
        name='typesetting_corrections'),
]
