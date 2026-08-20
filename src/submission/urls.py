__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
from django.urls import path
from django.urls import re_path

from submission import views

urlpatterns = [
    path("start/", views.start, name="submission_start"),
    re_path(r"^(?P<type>[-\w.]+)/start/$", views.start, name="submission_start"),
    path("<int:article_id>/info/", views.submit_info, name="submit_info"),
    path("<int:article_id>/authors/", views.submit_authors, name="submit_authors"),
    path(
        "<int:article_id>/authors/<int:author_id>/delete/",
        views.delete_author,
        name="delete_author",
    ),
    path(
        "<int:article_id>/authors/<int:author_id>/edit/",
        views.edit_author,
        name="submission_edit_author",
    ),
    path(
        "<int:article_id>/author/<int:author_id>/delete/",
        views.delete_frozen_author,
        name="submission_delete_frozen_author",
    ),
    path(
        "<int:article_id>/authors/<int:author_id>/link_to_account/",
        views.link_author_to_account,
        name="submission_link_author_to_account",
    ),
    # Affiliations
    path(
        "<int:article_id>/author/<int:author_id>/organization/search/",
        views.OrganizationListView.as_view(),
        name="submission_organization_search",
    ),
    path(
        "<int:article_id>/author/<int:author_id>/organization_name/create/",
        views.organization_name_create,
        name="submission_organization_name_create",
    ),
    path(
        "<int:article_id>/author/<int:author_id>/organization_name/<int:organization_name_id>/update/",
        views.organization_name_update,
        name="submission_organization_name_update",
    ),
    path(
        "<int:article_id>/author/<int:author_id>/organization/<int:organization_id>/affiliation/create/",
        views.affiliation_create,
        name="submission_affiliation_create",
    ),
    path(
        "<int:article_id>/author/<int:author_id>/affiliation/<int:affiliation_id>/update/",
        views.affiliation_update,
        name="submission_affiliation_update",
    ),
    re_path(
        r"^(?P<article_id>\d+)/author/(?P<author_id>\d+)/affiliation/update-from-orcid/(?P<how_many>primary|all)/$",
        views.affiliation_update_from_orcid,
        name="submission_affiliation_update_from_orcid",
    ),
    path(
        "<int:article_id>/author/<int:author_id>/affiliation/<int:affiliation_id>/delete/",
        views.affiliation_delete,
        name="submission_affiliation_delete",
    ),
    path("<int:article_id>/files/", views.submit_files, name="submit_files"),
    path("<int:article_id>/funding/", views.submit_funding, name="submit_funding"),
    path("submissions/", views.submit_submissions, name="submission_submissions"),
    path("<int:article_id>/review/", views.submit_review, name="submit_review"),
    path(
        "<int:article_id>/funders/<int:funder_id>/delete/",
        views.delete_funder,
        name="delete_funder",
    ),
    path(
        "<int:article_id>/funders/<int:funder_id>/edit/",
        views.edit_funder,
        name="edit_funder",
    ),
    path(
        "manager/article/settings/article/<int:article_id>/publishernotes/order/",
        views.publisher_notes_order,
        name="submission_article_publisher_notes_order",
    ),
    path("manager/configurator/", views.configurator, name="submission_configurator"),
    path("manager/additional_fields/", views.fields, name="submission_fields"),
    path(
        "manager/additional_fields/<int:field_id>/",
        views.fields,
        name="submission_fields_id",
    ),
    path("manager/licences/", views.licenses, name="submission_licenses"),
    re_path(
        r"^manager/licences/(?P<license_pk>\d+)/delete/",
        views.delete_license,
        name="submission_delete_license",
    ),
    re_path(
        r"^manager/licences/(?P<license_pk>\d+)/",
        views.licenses,
        name="submission_licenses_id",
    ),
]
