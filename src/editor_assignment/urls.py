__copyright__ = "Copyright 2026 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"


from django.urls import re_path

from editor_assignment import views


urlpatterns = [
    re_path(
        r"^$",
        views.unassigned,
        name="editor_assignment_list",
    ),
    re_path(
        r"^article/(?P<article_id>\d+)/$",
        views.unassigned_article,
        name="editor_assignment_article",
    ),
    re_path(
        r"^article/(?P<article_id>\d+)/assign/(?P<editor_id>\d+)/type/(?P<assignment_type>[-\w.]+)/$",
        views.assign_editor,
        name="editor_assignment_assign",
    ),
    re_path(
        r"^article/(?P<article_id>\d+)/assign/(?P<editor_id>\d+)/type/(?P<assignment_type>[-\w.]+)/"
        r"move/review/$",
        views.assign_editor_move_to_review,
        name="editor_assignment_assign_and_move",
    ),
    re_path(
        r"^article/(?P<article_id>\d+)/unassign/(?P<editor_id>\d+)/$",
        views.unassign_editor,
        name="editor_assignment_unassign",
    ),
    re_path(
        r"^article/(?P<article_id>\d+)/notify/(?P<editor_id>\d+)/$",
        views.assignment_notification,
        name="editor_assignment_notification",
    ),
    re_path(
        r"^article/(?P<article_id>\d+)/move/next/$",
        views.move_to_next_stage,
        name="editor_assignment_move_to_next_stage",
    ),
    # Backward-compat alias — the action is now generic. New code should
    # use editor_assignment_move_to_next_stage.
    re_path(
        r"^article/(?P<article_id>\d+)/move/review/$",
        views.move_to_next_stage,
        name="editor_assignment_move_to_review",
    ),
]
