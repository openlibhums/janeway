__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django.urls import path
from django.urls import re_path

from copyediting import views


urlpatterns = [
    # Editor URLs
    path("", views.copyediting, name="copyediting"),
    path(
        "article/<int:article_id>/",
        views.article_copyediting,
        name="article_copyediting",
    ),
    path(
        "article/<int:article_id>/assignment/add/",
        views.add_copyeditor_assignment,
        name="add_copyeditor_assignment",
    ),
    path(
        "article/<int:article_id>/assignment/<int:copyedit_id>/",
        views.notify_copyeditor_assignment,
        name="notify_copyeditor_assignment",
    ),
    path(
        "article/<int:article_id>/assignment/<int:copyedit_id>/edit/",
        views.edit_assignment,
        name="copyedit_edit_assignment",
    ),
    path(
        "article/<int:article_id>/assignment/<int:copyedit_id>/review/",
        views.editor_review,
        name="editor_review",
    ),
    path(
        "article/<int:article_id>/assignment/<int:copyedit_id>/author_review/<int:author_review_id>/",
        views.request_author_copyedit,
        name="request_author_copyedit",
    ),
    path(
        "article/<int:article_id>/assignment/<int:copyedit_id>/author_review/<int:author_review_id>/delete/",
        views.delete_author_review,
        name="delete_author_review",
    ),
    # Author URLs
    path(
        "author/article/<int:article_id>/assignment/<int:author_review_id>/",
        views.author_copyedit,
        name="author_copyedit",
    ),
    path(
        "author/article/<int:article_id>/assignment/<int:author_review_id>/file/<int:file_id>/update/",
        views.author_update_file,
        name="author_update_file",
    ),
    # Copyeditor URLs
    path("requests/", views.copyedit_requests, name="copyedit_requests"),
    path("requests/<int:copyedit_id>/", views.do_copyedit, name="do_copyedit"),
    path(
        "requests/<int:copyedit_id>/files/upload/",
        views.do_copyedit_add_file,
        name="do_copyedit_add_file",
    ),
    path(
        "requests/<int:copyedit_id>/files/<int:file_id>/download/",
        views.copyeditor_file,
        name="copyeditor_file",
    ),
    re_path(
        r"^requests/(?P<copyedit_id>\d+)/(?P<decision>accept|decline)/$",
        views.copyedit_request_decision,
        name="copyedit_request_decision",
    ),
]
