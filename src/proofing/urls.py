__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
from django.urls import path
from django.urls import re_path

from proofing import views

urlpatterns = [
    # PM
    path("", views.proofing_list, name="proofing_list"),
    path(
        "<int:article_id>/assign_manager/<int:user_id>/",
        views.proofing_assign_article,
        name="proofing_assign_article_with_user",
    ),
    path("<int:article_id>/", views.proofing_article, name="proofing_article"),
    path(
        "unassign/<int:article_id>/",
        views.proofing_unassign_article,
        name="proofing_unassign_article",
    ),
    path(
        "<int:article_id>/proofing_task/<int:proofing_task_id>/notify/",
        views.notify_proofreader,
        name="notify_proofreader",
    ),
    path(
        "<int:article_id>/proofing_task/<int:proofing_task_id>/edit/",
        views.edit_proofing_assignment,
        name="edit_proofing_assignment",
    ),
    path(
        "<int:article_id>/round/<int:round_id>/edit/",
        views.delete_proofing_round,
        name="delete_proofing_round",
    ),
    path(
        "<int:article_id>/proofing_task/<int:proofing_task_id>/review/",
        views.do_proofing,
        name="review_proofing_task",
    ),
    path(
        "<int:article_id>/proofing_task/<int:proofing_task_id>/corrections/",
        views.request_typesetting_changes,
        name="request_typesetting_changes",
    ),
    path(
        "<int:article_id>/proofing_task/<int:proofing_task_id>/corrections/<int:typeset_task_id>/notify/",
        views.notify_typesetter_changes,
        name="notify_typesetter_changes",
    ),
    re_path(
        r"^(?P<article_id>\d+)/ack/(?P<model_name>proofing|correction)/id/(?P<model_pk>\d+)/$",
        views.acknowledge,
        name="acknowledge_proofing",
    ),
    path(
        "<int:article_id>/complete/",
        views.complete_proofing,
        name="complete_proofing",
    ),
    # Proofreader
    path("requests/", views.proofing_requests, name="proofing_requests"),
    path("requests/<int:proofing_task_id>/", views.do_proofing, name="do_proofing"),
    re_path(
        r"^requests/(?P<proofing_task_id>\d+)/decision/(?P<decision>accept|decline)/$",
        views.proofing_requests,
        name="proofing_requests_decision",
    ),
    path(
        "requests/<int:proofing_task_id>/file/<int:file_id>/download/",
        views.proofing_download,
        name="proofing_download",
    ),
    re_path(
        r"^requests/(?P<proofing_task_id>\d+)/file/(?P<file_id>\d+)/download/galley.epub$",
        views.proofing_download,
        name="proofing_epub_download",
    ),
    path(
        "requests/<int:proofing_task_id>/preview/<int:galley_id>/",
        views.preview_galley,
        name="preview_galley",
    ),
    path(
        "requests/<int:proofing_task_id>/galley/<int:galley_id>/new_note/",
        views.new_note,
        name="proofing_new_note",
    ),
    path(
        "requests/<int:proofing_task_id>/galley/<int:galley_id>/delete/",
        views.delete_note,
        name="proofing_delete_note",
    ),
    re_path(
        r"^requests/(?P<proofing_task_id>\d+)/preview/(?P<galley_id>\d+)/(?P<file_name>.*)$",
        views.preview_figure,
        name="preview_figure",
    ),
    # Corrections
    path(
        "requests/corrections/",
        views.correction_requests,
        name="proofing_correction_requests",
    ),
    path(
        "requests/corrections/<int:typeset_task_id>/",
        views.typesetting_corrections,
        name="typesetting_corrections",
    ),
]
