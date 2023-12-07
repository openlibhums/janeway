__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django.urls import re_path

from repository import views

urlpatterns = [
    re_path(r'^dashboard/$',
        views.repository_dashboard,
        name='repository_dashboard'),

    re_path(r'^dashboard/(?P<preprint_id>\d+)/$',
        views.repository_author_article,
        name='repository_author_article'),

    re_path(r'^dashboard/(?P<preprint_id>\d+)/action/(?P<action>correction|version|metadata_correction)/$',
        views.repository_submit_update,
        name='repository_submit_update'),

    re_path(r'^about/$',
        views.repository_about,
        name='repository_about'),

    re_path(r'^search/$',
        views.repository_search,
        name='repository_search'),

    re_path(r'^search/(?P<search_term>.*)/$',
        views.repository_search,
        name='repository_search_with_term'),

    re_path(r'^view/(?P<preprint_id>\d+)/$',
        views.repository_preprint,
        name='repository_preprint'),

    re_path(r'^view/(?P<preprint_id>\d+)/pdf/$',
        views.repository_pdf,
        name='repository_pdf'),

    re_path(r'^object/(?P<preprint_id>\d+)/download/(?P<file_id>\d+)/$',
        views.repository_file_download,
        name='repository_file_download'),

    re_path(r'^list/$',
        views.repository_list,
        name='repository_list'),
    
    re_path(r'^list/subjects/$',
        views.repository_subject_list,
        name='repository_subject_list'),

    re_path(r'^list/(?P<subject_id>\d+)/$',
        views.repository_list,
        name='repository_list_subject'),

    re_path(r'^editors/$',
        views.preprints_editors,
        name='preprints_editors'),

    re_path(r'^submit/start/$',
        views.repository_submit,
        name='repository_submit'),

    re_path(r'^submit/(?P<preprint_id>\d+)/$',
        views.repository_submit,
        name='repository_submit_with_id'),

    re_path(r'^submit/(?P<preprint_id>\d+)/authors/$',
        views.repository_authors,
        name='repository_authors'),

    re_path(r'^submit/(?P<preprint_id>\d+)/authors/delete/(?P<redirect_string>[-\w]+)/$',
        views.repository_delete_author,
        name='repository_delete_author'),

    re_path(r'^submit/(?P<preprint_id>\d+)/authors/order/$',
        views.preprints_author_order,
        name='preprints_author_order'),

    re_path(r'^submit/(?P<preprint_id>\d+)/files/$',
        views.repository_files,
        name='repository_files'),

    re_path(r'^submit/(?P<preprint_id>\d+)/review/$',
        views.repository_review,
        name='repository_review'),

    re_path(r'^manager/$',
        views.preprints_manager,
        name='preprints_manager'),

    re_path(r'^manager/(?P<preprint_id>\d+)/$',
        views.repository_manager_article,
        name='repository_manager_article'),

    re_path(r'^manager/(?P<preprint_id>\d+)/edit/metadata/$',
        views.repository_edit_metadata,
        name='repository_edit_metadata'),
    re_path(r'^manager/(?P<preprint_id>\d+)/edit/authors/(?P<author_id>\d+)/$',
        views.repository_edit_author,
        name='repository_edit_authors'),
    re_path(r'^manager/(?P<preprint_id>\d+)/add/author/$',
        views.repository_edit_author,
        name='repository_add_author'),
    re_path(r'^manager/(?P<preprint_id>\d+)/author/order/$',
        views.reorder_preprint_authors,
        name='repository_manager_order_authors'),
    re_path(r'^manager/(?P<preprint_id>\d+)/author/delete/$',
        views.delete_preprint_author,
        name='repository_manager_delete_author'),

    # Review
    re_path(r'^manager/reviewers/$',
        views.manage_reviewers,
        name='repository_manage_reviewers'),
    re_path(r'^manager/(?P<preprint_id>\d+)/review/$',
        views.list_reviews,
        name='repository_list_reviews'),
    re_path(r'^manager/(?P<preprint_id>\d+)/review/new/$',
        views.manage_review,
        name='repository_new_review'),
    re_path(r'^manager/(?P<preprint_id>\d+)/review/(?P<review_id>\d+)/detail/$',
        views.review_detail,
        name='repository_review_detail'),
    re_path(r'^manager/(?P<preprint_id>\d+)/review/(?P<review_id>\d+)/notify/$',
        views.notify_reviewer,
        name='repository_notify_reviewer'),
    re_path(r'^manager/(?P<preprint_id>\d+)/review/(?P<review_id>\d+)/edit_comment/$',
        views.edit_review_comment,
        name='repository_edit_review_comment'),

    re_path(r'^review/(?P<review_id>\d+)/access_code/(?P<access_code>[0-9a-f-]+)/$',
        views.submit_review,
        name='repository_submit_review'),

    re_path(r'^review/(?P<review_id>\d+)/access_code/(?P<access_code>[0-9a-f-]+)/download/$',
        views.download_review_file,
        name='repository_download_review_file'),



    re_path(r'^manager/(?P<preprint_id>\d+)/download/(?P<file_id>\d+)/$',
        views.repository_download_file,
        name='repository_download_file'),

    re_path(r'^manager/(?P<preprint_id>\d+)/notification/$',
        views.repository_notification,
        name='repository_notification'),

    re_path(r'^manager/(?P<preprint_id>\d+)/log/$',
        views.repository_preprint_log,
        name='repository_preprint_log'),

    re_path(r'^manager/(?P<preprint_id>\d+)/comments/$',
        views.repository_comments,
        name='repository_comments'),

    re_path(r'^manager/(?P<preprint_id>\d+)/supp_files/$',
        views.manage_supplementary_files,
        name='repository_manage_supplementary_files'),

    re_path(r'^manager/(?P<preprint_id>\d+)/supp_files/new/$',
        views.new_supplementary_file,
        name='repository_new_supplementary_files'),

    re_path(r'^manager/(?P<preprint_id>\d+)/supp_files/order/$',
        views.order_supplementary_files,
        name='repository_order_supplementary_files'),

    re_path(r'^manager/(?P<preprint_id>\d+)/supp_files/delete/$',
        views.delete_supplementary_file,
        name='repository_delete_supplementary_files'),

    re_path(r'^manager/licenses/$',
        views.repository_licenses,
        name='repository_licenses'),

    re_path(r'^manager/subjects/$',
        views.repository_subjects,
        name='repository_subjects'),

    re_path(r'^manager/subjects/delete/$',
        views.repository_delete_subject,
        name='repository_delete_subject'),

    re_path(r'^manager/subjects/(?P<subject_id>\d+)/$',
        views.repository_subjects,
        name='repository_subjects_with_id'),

    re_path(r'^manager/rejected/$',
        views.repository_rejected_submissions,
        name='repository_rejected_submissions'),

    re_path(r'^manager/orphans/$',
        views.orphaned_preprints,
        name='preprints_orphaned_preprints'),

    re_path(r'^manager/versions/$',
        views.version_queue,
        name='version_queue'),

    re_path(r'^wizard/$',
        views.repository_wizard,
        name='repository_wizard'),

    re_path(r'^wizard/repository/(?P<short_name>[-\w]+)/step/(?P<step>\d+)/$',
        views.repository_wizard,
        name='repository_wizard_with_id'),

    re_path(r'^manager/fields/$',
        views.repository_fields,
        name='repository_fields'),

    re_path(r'^manager/fields/delete/$',
        views.repository_delete_field,
        name='repository_delete_field'),

    re_path(r'^manager/fields/order/$',
        views.repository_order_fields,
        name='repository_order_fields'),

    re_path(r'^manager/fields/(?P<field_id>\d+)/$',
        views.repository_fields,
        name='repository_fields_with_id'),

    re_path(r'^manager/(?P<preprint_id>\d+)/send_to_journal/$',
        views.send_preprint_to_journal,
        name='repository_send_to_a_journal'),
    re_path(r'^manager/(?P<preprint_id>\d+)/send_to_journal/(?P<journal_id>\d+)/$',
        views.send_preprint_to_journal,
        name='repository_send_to_journal'),
    re_path(r'^manager/recommendations/$',
        views.list_review_recommendations,
        name='repository_list_review_recommendations'),
    re_path(r'^manager/recommendations/create/$',
        views.manage_review_recommendation,
        name='repository_create_review_recommendation'),
    re_path(r'^manager/recommendations/(?P<recommendation_id>\d+)/edit/$',
        views.manage_review_recommendation,
        name='repository_edit_review_recommendation'),

    # Popup email
    re_path(r'^email/user/(?P<user_id>\d+)/preprint/(?P<preprint_id>\d+)/$',
        views.send_user_email, name='send_user_email_preprint'),
]
