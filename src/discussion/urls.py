__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve, Andy Byers & Mauro Sanchez"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.urls import re_path
from discussion import views, partial_views

urlpatterns = [
    # === Full page views ===
    # Base threads page — shell for HTMX interface
    re_path(
        r"^(?P<object_type>preprint|article)/(?P<object_id>\d+)/$",
        views.threads,
        name="discussion_threads",
    ),
    # Legacy thread view
    re_path(
        r"^(?P<object_type>preprint|article)/(?P<object_id>\d+)/thread/(?P<thread_id>\d+)/$",
        views.threads,
        name="discussion_thread_legacy",
    ),
    # New full page thread view (this is what we push with hx-push-url)
    re_path(
        r"^(?P<object_type>preprint|article)/(?P<object_id>\d+)/threads/(?P<thread_id>\d+)/$",
        views.threads,
        name="discussion_thread",
    ),
    # Post
    re_path(
        r"^thread/(?P<thread_id>\d+)/post/new/$",
        views.add_post,
        name="discussion_add_post",
    ),
    # === HTMX partials ===
    # Sidebar list
    re_path(
        r"^(?P<object_type>preprint|article)/(?P<object_id>\d+)/threads/list/$",
        partial_views.threads_list_partial,
        name="discussion_threads_list_partial",
    ),
    # Thread detail fragment — now at `/partial/`
    re_path(
        r"^(?P<object_type>preprint|article)/(?P<object_id>\d+)/threads/(?P<thread_id>\d+)/partial/$",
        partial_views.thread_detail_partial,
        name="discussion_thread_detail_partial",
    ),
    # Modal for new thread creation
    re_path(
        r"^(?P<object_type>preprint|article)/(?P<object_id>\d+)/threads/new/$",
        partial_views.new_thread_form_partial,
        name="discussion_new_thread_modal",
    ),
    # Handle new thread creation (POST)
    re_path(
        r"^(?P<object_type>preprint|article)/(?P<object_id>\d+)/threads/create/$",
        views.create_thread,
        name="discussion_create_thread",
    ),
    re_path(
        r"^threads/(?P<thread_id>\d+)/invite/search/$",
        views.ThreadInviteUserListView.as_view(),
        name="discussion_invite_search",
    ),
    re_path(
        r"^threads/(?P<thread_id>\d+)/invite/add/$",
        views.add_participant,
        name="discussion_add_participant",
    ),
]

