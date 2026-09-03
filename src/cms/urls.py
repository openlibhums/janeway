__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django.urls import path
from django.urls import re_path

from cms import views

urlpatterns = [
    # Probably needs some multi-journal logic here
    path("", views.index, name="cms_index"),
    path("page/new/", views.page_manage, name="cms_page_new"),
    path("page/<int:page_id>/", views.page_manage, name="cms_page_edit"),
    re_path(r"^(?P<page_name>w+?)$", views.view_page, name="cms_page"),
    path("nav/", views.nav, name="cms_nav"),
    path("nav/<int:nav_id>/", views.nav, name="cms_nav_edit"),
    path("submission_items/", views.submission_items, name="cms_submission_items"),
    path(
        "submission_items/add/",
        views.order_submission_items,
        name="cms_order_submission_items",
    ),
    path(
        "submission_items/order/",
        views.edit_or_create_submission_item,
        name="cms_add_submission_item",
    ),
    path(
        "submission_items/<int:item_id>/",
        views.edit_or_create_submission_item,
        name="cms_edit_submission_item",
    ),
    path(
        "media_files/",
        views.file_list,
        name="cms_file_list",
    ),
    path(
        "media_files/upload/",
        views.file_upload,
        name="cms_file_upload",
    ),
]
