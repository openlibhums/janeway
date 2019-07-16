__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
from django.conf.urls import url

from production import views

urlpatterns = [
    # Editor
    url(r'^$',
        views.production_list,
        name='production_list'),
    url(r'^(?P<article_id>\d+)/no_assignment/$',
        views.non_workflow_assign_article,
        name='production_non_workflow_assign'),

    # Production Manager
    url(r'^(?P<article_id>\d+)/$',
        views.production_article,
        name='production_article'),
    url(
        r'^(?P<article_id>\d+)/preview/(?P<galley_id>\d+)/$',
        views.preview_galley,
        name='production_preview_galley'
        ),
    url(r'^(?P<article_id>\d+)/preview/(?P<galley_id>\d+)/(?P<file_name>.*)$',
        views.preview_figure,
        name='production_preview_figure'
        ),
    url(r'^assign/(?P<article_id>\d+)/user/(?P<user_id>\d+)$',
        views.production_assign_article,
        name='production_assign_article'),
    url(r'^unassign/(?P<article_id>\d+)/$',
        views.production_unassign_article,
        name='production_unassign_article'),
    url(r'^(?P<article_id>\d+)/galley/(?P<galley_id>\d+)/$',
        views.edit_galley,
        name='pm_edit_galley'),
    url(r'^(?P<article_id>\d+)/task/(?P<typeset_id>\d+)/reviewed/$',
        views.review_typeset_task,
        name='review_typeset_task'),
    url(r'^(?P<article_id>\d+)/done/$',
        views.production_done, name='production_done'),

    # Typeset Assignment
    url(r'^(?P<article_id>\d+)/assignment/(?P<production_assignment_id>\d+)/typeset/assign/$',
        views.assign_typesetter, name='assign_typesetter'),
    url(r'^typeset/(?P<typeset_id>\d+)/notify/$',
        views.notify_typesetter, name='notify_typesetter'),
    url(r'^typeset/(?P<typeset_id>\d+)/notify/event/(?P<event>true|false)$',
        views.notify_typesetter, name='notify_typesetter_event'),
    url(r'^typeset/(?P<typeset_id>\d+)/delete/$',
        views.edit_typesetter_assignment, name='edit_typesetter_assignment'),

    url(r'^(?P<article_id>\d+)/supp_file/(?P<supp_file_id>\d+)/doi/$',
        views.supp_file_doi,
        name='supp_file_doi'),

    # Typesetter
    url(r'^requests/$',
        views.typesetter_requests,
        name='typesetter_requests'),
    url(r'^requests/(?P<typeset_id>\d+)/decision/(?P<decision>accept|decline)/$',
        views.typesetter_requests,
        name='typesetter_requests_decision'),
    url(r'^requests/(?P<typeset_id>\d+)/$',
        views.do_typeset_task,
        name='do_typeset_task'),
    url(r'^requests/(?P<typeset_id>\d+)/galley/(?P<galley_id>\d+)/$',
        views.edit_galley,
        name='edit_galley'),
    url(r'^requests/(?P<typeset_id>\d+)/galley/(?P<galley_id>\d+)/delete/$',
        views.delete_galley,
        name='delete_galley'),
]
