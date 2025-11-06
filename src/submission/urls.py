__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
from django.urls import re_path

from submission import views

urlpatterns = [
    re_path(r"^start/$", views.start, name="submission_start"),
    re_path(r"^(?P<type>[-\w.]+)/start/$", views.start, name="submission_start"),
    re_path(r"^(?P<article_id>\d+)/info/$", views.submit_info, name="submit_info"),
    re_path(
        r"^(?P<article_id>\d+)/authors/$", views.submit_authors, name="submit_authors"
    ),
    re_path(
        r"^(?P<article_id>\d+)/authors/(?P<author_id>\d+)/delete/$",
        views.delete_author,
        name="delete_author",
    ),
    re_path(
        r"^(?P<article_id>\d+)/authors/(?P<author_id>\d+)/edit/$",
        views.edit_author,
        name="submission_edit_author",
    ),
    re_path(
        r"^(?P<article_id>\d+)/author/(?P<author_id>\d+)/delete/$",
        views.delete_frozen_author,
        name="submission_delete_frozen_author",
    ),
    # Affiliations
    re_path(
        r"^(?P<article_id>\d+)/author/(?P<author_id>\d+)/organization/search/$",
        views.OrganizationListView.as_view(),
        name="submission_organization_search",
    ),
    re_path(
        r"^(?P<article_id>\d+)/author/(?P<author_id>\d+)/organization_name/create/$",
        views.organization_name_create,
        name="submission_organization_name_create",
    ),
    re_path(
        r"^(?P<article_id>\d+)/author/(?P<author_id>\d+)/organization_name/(?P<organization_name_id>\d+)/update/$",
        views.organization_name_update,
        name="submission_organization_name_update",
    ),
    re_path(
        r"^(?P<article_id>\d+)/author/(?P<author_id>\d+)/organization/(?P<organization_id>\d+)/affiliation/create/$",
        views.affiliation_create,
        name="submission_affiliation_create",
    ),
    re_path(
        r"^(?P<article_id>\d+)/author/(?P<author_id>\d+)/affiliation/(?P<affiliation_id>\d+)/update/$",
        views.affiliation_update,
        name="submission_affiliation_update",
    ),
    re_path(
        r"^(?P<article_id>\d+)/author/(?P<author_id>\d+)/affiliation/update-from-orcid/(?P<how_many>primary|all)/$",
        views.affiliation_update_from_orcid,
        name="submission_affiliation_update_from_orcid",
    ),
    re_path(
        r"^(?P<article_id>\d+)/author/(?P<author_id>\d+)/affiliation/(?P<affiliation_id>\d+)/delete/$",
        views.affiliation_delete,
        name="submission_affiliation_delete",
    ),
    re_path(r"^(?P<article_id>\d+)/files/$", views.submit_files, name="submit_files"),
    re_path(
        r"^(?P<article_id>\d+)/funding/$", views.submit_funding, name="submit_funding"
    ),
    re_path(r"^submissions/$", views.submit_submissions, name="submission_submissions"),
    re_path(
        r"^(?P<article_id>\d+)/review/$", views.submit_review, name="submit_review"
    ),
    re_path(
        r"^(?P<article_id>\d+)/funders/(?P<funder_id>\d+)/delete/$",
        views.delete_funder,
        name="delete_funder",
    ),
    re_path(
        r"^(?P<article_id>\d+)/funders/(?P<funder_id>\d+)/edit/$",
        views.edit_funder,
        name="edit_funder",
    ),
    re_path(
        r"^manager/article/settings/article/(?P<article_id>\d+)/publishernotes/order/$",
        views.publisher_notes_order,
        name="submission_article_publisher_notes_order",
    ),
    re_path(
        r"^manager/configurator/$", views.configurator, name="submission_configurator"
    ),
    re_path(r"^manager/additional_fields/$", views.fields, name="submission_fields"),
    re_path(
        r"^manager/additional_fields/(?P<field_id>\d+)/$",
        views.fields,
        name="submission_fields_id",
    ),
    re_path(r"^manager/licences/$", views.licenses, name="submission_licenses"),
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
