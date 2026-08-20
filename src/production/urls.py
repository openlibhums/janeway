__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
from django.urls import path
from django.urls import re_path

from production import views

urlpatterns = [
    # Editor
    path("", views.production_list, name="production_list"),
    path(
        "<int:article_id>/no_assignment/",
        views.non_workflow_assign_article,
        name="production_non_workflow_assign",
    ),
    # Production Manager
    path("<int:article_id>/", views.production_article, name="production_article"),
    path(
        "<int:article_id>/preview/<int:galley_id>/",
        views.preview_galley,
        name="production_preview_galley",
    ),
    re_path(
        r"^(?P<article_id>\d+)/preview/(?P<galley_id>\d+)/(?P<file_name>.*)$",
        views.preview_figure,
        name="production_preview_figure",
    ),
    path(
        "assign/<int:article_id>/user/<int:user_id>",
        views.production_assign_article,
        name="production_assign_article",
    ),
    path(
        "unassign/<int:article_id>/",
        views.production_unassign_article,
        name="production_unassign_article",
    ),
    path(
        "<int:article_id>/galley/<int:galley_id>/",
        views.edit_galley,
        name="pm_edit_galley",
    ),
    path(
        "<int:article_id>/galley/<int:galley_id>/zip_uploader/",
        views.upload_image_zip,
        name="pm_zip_uploader",
    ),
    path(
        "<int:article_id>/task/<int:typeset_id>/reviewed/",
        views.review_typeset_task,
        name="review_typeset_task",
    ),
    path("<int:article_id>/done/", views.production_done, name="production_done"),
    # Typeset Assignment
    path(
        "<int:article_id>/assignment/<int:production_assignment_id>/typeset/assign/",
        views.assign_typesetter,
        name="assign_typesetter",
    ),
    path(
        "typeset/<int:typeset_id>/notify/",
        views.notify_typesetter,
        name="notify_typesetter",
    ),
    re_path(
        r"^typeset/(?P<typeset_id>\d+)/notify/event/(?P<event>true|false)$",
        views.notify_typesetter,
        name="notify_typesetter_event",
    ),
    path(
        "typeset/<int:typeset_id>/delete/",
        views.edit_typesetter_assignment,
        name="edit_typesetter_assignment",
    ),
    path(
        "<int:article_id>/supp_file/<int:supp_file_id>/doi/",
        views.supp_file_doi,
        name="supp_file_doi",
    ),
    # Typesetter
    path("requests/", views.typesetter_requests, name="typesetter_requests"),
    re_path(
        r"^requests/(?P<typeset_id>\d+)/decision/(?P<decision>accept|decline)/$",
        views.typesetter_requests,
        name="typesetter_requests_decision",
    ),
    path(
        "requests/<int:typeset_id>/",
        views.do_typeset_task,
        name="do_typeset_task",
    ),
    path(
        "requests/<int:typeset_id>/galley/<int:galley_id>/",
        views.edit_galley,
        name="edit_galley",
    ),
    path(
        "requests/<int:typeset_id>/galley/<int:galley_id>/zip_uploader/",
        views.upload_image_zip,
        name="typesetter_zip_uploader",
    ),
    path(
        "requests/<int:typeset_id>/galley/<int:galley_id>/delete/",
        views.delete_galley,
        name="delete_galley",
    ),
]
