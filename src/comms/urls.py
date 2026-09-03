from django.urls import path
from django.urls import re_path

from comms import views

urlpatterns = [
    path("", views.news_list, name="core_news_list"),
    re_path(r"^tag/(?P<tag>.*)/$", views.news_list, name="core_news_list_tag"),
    re_path(
        r"^(?P<presswide>all)/$",
        views.news_list,
        name="core_news_list_presswide",
    ),
    re_path(
        r"^(?P<presswide>all)/tag/(?P<tag>.*)/$",
        views.news_list,
        name="core_news_list_tag_presswide",
    ),
    path("<int:news_pk>/", views.news_item, name="core_news_item"),
    re_path(
        r"^(?P<identifier_type>.+?)/(?P<identifier>.+)/image/(?P<file_id>\d+|None)/$",
        views.serve_news_file,
        name="news_file_download",
    ),
    path(
        "manager/",
        views.manage_news_list,
        name="core_manager_news",
    ),
    path(
        "manager/new/",
        views.manage_news,
        name="core_manager_create_news",
    ),
    path(
        "manager/edit/<int:news_pk>/",
        views.manage_news,
        name="core_manager_edit_news",
    ),
]
