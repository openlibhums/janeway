__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django.conf.urls import url

from review import views

urlpatterns = [
    url(r'^$', views.home, name='review_home'),
    url(r'^unassigned/$', views.unassigned, name='review_unassigned'),
    url(
        r'^unassigned/article/(?P<article_id>\d+)/$',
        views.unassigned_article,
        name='review_unassigned_article',
    ),
    url(
        r'^unassigned/article/(?P<article_id>\d+)/projected_issue/$',
        views.add_projected_issue,
        name='review_projected_issue',
    ),
    url(r'^unassigned/article/(?P<article_id>\d+)/assign/(?P<editor_id>\d+)/type/(?P<assignment_type>[-\w.]+)/$',
        views.assign_editor, name='review_assign_editor'),
    url(r'^unassigned/article/(?P<article_id>\d+)/assign/(?P<editor_id>\d+)/type/(?P<assignment_type>[-\w.]+)/'
        r'move/review/$',
        views.assign_editor_move_to_review, name='review_assign_editor_and_move_to_review'),
    url(r'^unassigned/article/(?P<article_id>\d+)/unassign/(?P<editor_id>\d+)/$', views.unassign_editor,
        name='review_unassign_editor'),
    url(r'^unassigned/article/(?P<article_id>\d+)/notify/(?P<editor_id>\d+)/$', views.assignment_notification,
        name='review_assignment_notification'),
    url(r'^unassigned/article/(?P<article_id>\d+)/move/review/$', views.move_to_review, name='review_move_to_review'),
    url(r'^article/(?P<article_id>\d+)/crosscheck/$', views.view_ithenticate_report, name='review_crosscheck'),
    url(r'^article/(?P<article_id>\d+)/move/(?P<decision>accept|decline|undecline)/$', views.review_decision,
        name='review_decision'),
    url(r'^article/(?P<article_id>\d+)/summary/$', views.unassigned_article, name='review_summary'),
    url(r'^article/(?P<article_id>\d+)/$', views.in_review, name='review_in_review'),
    url(r'^article/(?P<article_id>\d+)/round/(?P<round_id>\d+)/delete/$', views.delete_review_round,
        name='review_delete_review_round'),
    url(r'^article/(?P<article_id>\d+)/round/(?P<round_id>\d+)/files/add/$', views.add_files, name='review_add_files'),
    url(r'^article/(?P<article_id>\d+)/round/(?P<round_id>\d+)/files/(?P<file_id>\d+)/remove/$', views.remove_file,
        name='review_remove_file'),

    url(r'^article/(?P<article_id>\d+)/review/add/$', views.add_review_assignment, name='review_add_review_assignment'),
    url(r'^article/(?P<article_id>\d+)/review/(?P<review_id>\d+)/notify/$', views.notify_reviewer,
        name='review_notify_reviewer'),
    url(r'^article/(?P<article_id>\d+)/review/(?P<review_id>\d+)/view/$', views.view_review,
        name='review_view_review'),
    url(r'^article/(?P<article_id>\d+)/review/(?P<review_id>\d+)/answer/(?P<answer_id>\d+)/$', views.edit_review_answer,
        name='review_edit_review_answer'),
    url(r'^article/(?P<article_id>\d+)/review/(?P<review_id>\d+)/edit/$', views.edit_review,
        name='review_edit_review'),
    url(r'^article/(?P<article_id>\d+)/review/(?P<review_id>\d+)/delete/$', views.delete_review,
        name='review_delete_review'),
    url(r'^article/(?P<article_id>\d+)/review/(?P<review_id>\d+)/withdraw/$', views.withdraw_review,
        name='review_withdraw_review'),
    url(r'^article/(?P<article_id>\d+)/review/(?P<review_id>\d+)/reset/$', views.reset_review,
        name='review_reset_review'),
    url(r'^article/(?P<article_id>\d+)/review/(?P<review_id>\d+)/rate/$', views.rate_reviewer,
        name='review_rate_reviewer'),
    url(r'article/(?P<article_id>\d+)/review/(?P<review_id>\d+)/reminder/(?P<reminder_type>request|accepted)/',
        views.send_review_reminder,
        name='review_send_reminder'),

    url(r'^article/(?P<article_id>\d+)/revisions/request/$', views.request_revisions,
        name='review_request_revisions'),
    url(r'^article/(?P<article_id>\d+)/revisions/(?P<revision_id>\d+)/notify/$', views.request_revisions_notification,
        name='request_revisions_notification'),
    url(r'^article/(?P<article_id>\d+)/revisions/(?P<revision_id>\d+)/edit/$', views.edit_revision_request,
        name='edit_revision_request'),
    url(r'^article/(?P<article_id>\d+)/revisions/(?P<revision_id>\d+)/$', views.do_revisions,
        name='do_revisions'),
    url(r'^article/(?P<article_id>\d+)/revisions/(?P<revision_id>\d+)/update/file/(?P<file_id>\d+)$',
        views.replace_file, name='revisions_replace_file'),
    url(r'^article/(?P<article_id>\d+)/revisions/(?P<revision_id>\d+)/upload/file/$',
        views.upload_new_file, name='revisions_upload_new_file'),
    url(r'^article/(?P<article_id>\d+)/revisions/(?P<revision_id>\d+)/view/$',
        views.view_revision, name='view_revision'),

    url(r'^article/(?P<article_id>\d+)/decision/draft/$', views.draft_decision,
        name='review_draft_decision'),
    url(r'^article/(?P<article_id>\d+)/decision/draft/(?P<draft_id>\d+)/$', views.edit_draft_decision,
        name='review_edit_draft_decision'),
    url(r'^article/(?P<article_id>\d+)/decision/draft/(?P<draft_id>\d+)/action/$', views.manage_draft,
        name='review_manage_draft'),
    url(r'^article/(?P<article_id>\d+)/decision/draft/text/$', views.draft_decision_text,
        name='review_draft_decision_text'),

    url(r'^requests/$', views.review_requests, name='review_requests'),
    url(r'^requests/(?P<assignment_id>\d+)/accept/$', views.accept_review_request, name='accept_review'),
    url(r'^requests/(?P<assignment_id>\d+)/decline/$', views.decline_review_request, name='decline_review'),
    url(r'^requests/(?P<assignment_id>\d+)/decline/suggest/$', views.suggest_reviewers, name='suggest_reviewers'),
    url(r'^requests/(?P<assignment_id>\d+)/thanks/$', views.thanks_review, name='thanks_review'),
    url(r'^requests/(?P<assignment_id>\d+)/annotation/$', views.hypothesis_review, name='hypothesis_review'),
    url(r'^requests/(?P<assignment_id>\d+)/$',
        views.do_review,
        name='do_review'),
    url(r'^requests/(?P<assignment_id>\d+)/upload_file/$',
        views.upload_review_file,
        name='upload_review_file'),


    url(r'^author/(?P<article_id>\d+)/$', views.author_view_reviews, name='review_author_view'),

    url(r'^editor/(?P<article_id>\d+)/file_download/(?P<file_id>\d+)/$', views.editor_article_file,
        name='editor_file_download'),

    url(r'^reviewer/(?P<assignment_id>\d+)/file_download/(?P<file_id>\d+)/$', views.reviewer_article_file,
        name='review_file_download'),
    url(r'^reviewer/(?P<assignment_id>\d+)/file_download/all/$', views.review_download_all_files,
        name='review_download_all_files'),

    url(r'^article/(?P<article_id>\d+)/access_denied/$', views.review_warning, name='review_warning'),

    # Review forms
    url(r'^manager/forms/$',
        views.review_forms,
        name='review_review_forms'),
    url(r'^manager/form/(?P<form_id>\d+)/$',
        views.edit_review_form,
        name='edit_review_form'),
    url(r'^manager/form/(?P<form_id>\d+)/preview/$',
        views.preview_form,
        name='preview_form'),
    url(r'^manager/form/(?P<form_id>\d+)/order_elements/$',
        views.order_review_elements,
        name='order_review_elements'),
    url(r'^manager/form/(?P<form_id>\d+)/element/(?P<element_id>\d+)/$',
        views.edit_review_form,
        name='edit_review_form_element'),

    url(r'^article/(?P<article_id>\d+)/decision_helper/$',
        views.decision_helper,
        name='decision_helper',
        )
]
