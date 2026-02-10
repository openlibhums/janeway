__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve, Andy Byers & Mauro Sanchez"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.urls import re_path
from discussion import views, partial_views

urlpatterns = [
    re_path(
        r"^(?P<object_type>preprint|article)/(?P<object_id>\d+)/$",
        views.threads,
        name="discussion_threads",
    ),
    re_path(
        r"^(?P<object_type>preprint|article)/(?P<object_id>\d+)/thread/(?P<thread_id>\d+)/$",
        views.threads,
        name="discussion_thread_legacy",
    ),
    re_path(
        r"^(?P<object_type>preprint|article)/(?P<object_id>\d+)/threads/(?P<thread_id>\d+)/$",
        views.threads,
        name="discussion_thread",
    ),
    re_path(
        r"^thread/(?P<thread_id>\d+)/post/new/$",
        partial_views.add_post,
        name="discussion_add_post",
    ),
    re_path(
        r"^(?P<object_type>preprint|article)/(?P<object_id>\d+)/threads/list/$",
        partial_views.threads_list_partial,
        name="discussion_threads_list_partial",
    ),
    re_path(
        r"^(?P<object_type>preprint|article)/(?P<object_id>\d+)/threads/(?P<thread_id>\d+)/partial/$",
        partial_views.thread_detail_partial,
        name="discussion_thread_detail_partial",
    ),
    re_path(
        r"^(?P<object_type>preprint|article)/(?P<object_id>\d+)/threads/new/$",
        partial_views.new_thread_form_partial,
        name="discussion_new_thread_modal",
    ),
    re_path(
        r"^(?P<object_type>preprint|article)/(?P<object_id>\d+)/threads/create/$",
        partial_views.create_thread,
        name="discussion_create_thread",
    ),
    re_path(
        r"^thread/(?P<thread_id>\d+)/post/(?P<post_id>\d+)/edit/$",
        partial_views.edit_post,
        name="discussion_edit_post",
    ),
    re_path(
        r"^thread/(?P<thread_id>\d+)/edit-subject/$",
        partial_views.edit_subject,
        name="discussion_edit_subject",
    ),
    re_path(
        r"^thread/(?P<thread_id>\d+)/file/(?P<file_id>\d+)/$",
        partial_views.serve_discussion_file,
        name="discussion_serve_file",
    ),
    re_path(
        r"^threads/(?P<thread_id>\d+)/invite/search/$",
        partial_views.ThreadInviteUserListView.as_view(),
        name="discussion_invite_search",
    ),
    re_path(
        r"^threads/(?P<thread_id>\d+)/invite/add/$",
        partial_views.add_participant,
        name="discussion_add_participant",
    ),
    re_path(
        r"^threads/(?P<thread_id>\d+)/invite/remove/$",
        partial_views.remove_participant,
        name="discussion_remove_participant",
    ),
]

