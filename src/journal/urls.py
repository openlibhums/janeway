__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.urls import path, re_path

from journal import views
from identifiers.models import NON_DOI_IDENTIFIER_TYPES, DOI_REGEX_PATTERN

NON_DOI_PIPE_SEPARATED_IDENTIFIERS = "|".join(NON_DOI_IDENTIFIER_TYPES)

# Various url patterns in this module have duplicated names
# This is so we can handle DOI patterns using a more restrictive
# Regex pattern an example is this is 'article_view'

urlpatterns = [
    # Figures and download patterns
    re_path(
        r"^article/(?P<identifier_type>{0})/(?P<identifier>[\w.-]+)/print/$"
        "".format(NON_DOI_PIPE_SEPARATED_IDENTIFIERS),
        views.print_article,
        name="article_print_article",
    ),
    re_path(
        r"^article/(?P<article_id>\d+)/galley/(?P<galley_id>\d+)/figure/(?P<file_name>.*)/$",
        views.article_figure,
        name="article_galley_figure",
    ),
    re_path(
        r"^article/(?P<identifier_type>id)/(?P<identifier>.+)/file/(?P<file_id>\d+)/replace$",
        views.replace_article_file,
        name="article_file_replace",
    ),
    re_path(
        r"^article/(?P<identifier_type>id)/(?P<identifier>.+)/file/(?P<file_id>\d+|None)/$",
        views.serve_article_file,
        name="article_file_download",
    ),
    re_path(
        r"^article/(?P<identifier_type>id)/(?P<identifier>.+)/file_history/(?P<file_id>\d+|None)/$",
        views.serve_article_file_history,
        name="article_file_history_download",
    ),
    re_path(
        r"^article/(?P<article_id>\d+)/galley/(?P<galley_id>\d+)/download/",
        views.download_galley,
        name="article_download_galley",
    ),
    re_path(
        r"^article/(?P<article_id>\d+)/galley/(?P<galley_id>\d+)/view/",
        views.view_galley,
        name="article_view_galley",
    ),
    re_path(
        r"^article/(?P<identifier_type>id)/(?P<identifier>.+)/download/pdf/$",
        views.serve_article_pdf,
        name="serve_article_pdf",
    ),
    re_path(
        r"^article/(?P<identifier_type>id)/(?P<identifier>.+)/download/xml/$",
        views.serve_article_xml,
        name="serve_article_xml",
    ),
    re_path(
        r"^article/(?P<identifier_type>id)/(?P<identifier>.+)/download/ris/$",
        views.serve_article_ris,
        name="serve_article_ris",
    ),
    re_path(
        r"^article/(?P<identifier_type>id)/(?P<identifier>.+)/download/bib/$",
        views.serve_article_bib,
        name="serve_article_bib",
    ),
    re_path(
        r"^article/(?P<identifier_type>{0})/(?P<identifier>[\w.-]+)/table/(?P<table_name>.+)$"
        "".format(NON_DOI_PIPE_SEPARATED_IDENTIFIERS),
        views.download_table,
        name="article_table",
    ),
    re_path(
        r"^article/(?P<identifier_type>{0})/(?P<identifier>[\w.-]+)/(?P<file_name>.+)$"
        "".format(NON_DOI_PIPE_SEPARATED_IDENTIFIERS),
        views.identifier_figure,
        name="article_figure",
    ),
    path(
        "articles/",
        views.PublishedArticlesListView.as_view(),
        name="journal_articles",
    ),
    # Issues/Collections
    path("issues/", views.issues, name="journal_issues"),
    path("issue/current/", views.current_issue, name="current_issue"),
    path("issue/<int:issue_id>/info/", views.issue, name="journal_issue"),
    path(
        "issue/<int:issue_id>/download/<int:galley_id>",
        views.download_issue_galley,
        name="journal_issue_download_galley",
    ),
    path("collections/", views.collections, name="journal_collections_type"),
    path(
        "collections/<int:collection_id>/",
        views.collection,
        name="journal_collection",
    ),
    # The URLS below are roughly equivalent but we need both because of backwards compatibility reasons
    re_path(
        r"^collections/(?P<issue_type_code>[a-zA-Z-_]+)/$",
        views.collections,
        name="journal_collections",
    ),
    re_path(
        r"^collections/type/(?P<issue_type_code>[\da-zA-Z-_]+)/$",
        views.collections,
        name="journal_collections_with_digits",
    ),
    # The URLS below are roughly equivalent but we need both because of backwards compatibility reasons
    re_path(
        r"^collection/(?P<collection_code>[a-zA-Z-_]+)/$",
        views.collection_by_code,
        name="journal_collection_by_code",
    ),
    re_path(
        r"^collection/code/(?P<collection_code>[\da-zA-Z-_]+)/$",
        views.collection_by_code,
        name="journal_collection_by_code_with_digits",
    ),
    path("cover/", views.serve_journal_cover, name="journal_cover_download"),
    path(
        "volume/<int:volume_number>/issue/<int:issue_number>/",
        views.volume,
        name="journal_volume",
    ),
    # Article patterns
    re_path(
        r"^article/(?P<identifier_type>{0})/(?P<identifier>[\w.-]+)/edit/$"
        "".format(NON_DOI_PIPE_SEPARATED_IDENTIFIERS),
        views.edit_article,
        name="article_edit",
    ),
    re_path(
        r"^article/(?P<identifier_type>{0})/(?P<identifier>[\w.-]+)/$"
        "".format(NON_DOI_PIPE_SEPARATED_IDENTIFIERS),
        views.article,
        name="article_view",
    ),
    re_path(
        r"^article/(?P<identifier_type>doi)/(?P<identifier>{0})/$"
        "".format(DOI_REGEX_PATTERN),
        views.doi_redirect,
        name="doi_redirect",
    ),
    re_path(
        r"^article/(?P<identifier_type>[\w.-_]+)/(?P<identifier>[\w.-]+)/$",
        views.article_from_identifier,
        name="article_view_custom_identifier",
    ),
    # File management
    path(
        "<int:article_id>/files/management/",
        views.document_management,
        name="document_management",
    ),
    path(
        "<int:article_id>/files/<int:file_id>/info/",
        views.submit_files_info,
        name="submit_replacement_files_info",
    ),
    path(
        "<int:article_id>/files/<int:file_id>/history/",
        views.file_history,
        name="file_history",
    ),
    path(
        "<int:article_id>/files/<int:file_id>/delete/",
        views.file_delete,
        name="file_delete",
    ),
    path(
        "<int:article_id>/files/<int:file_id>/old/<int:file_history_id>/reinstate/",
        views.file_reinstate,
        name="file_reinstate",
    ),
    path(
        "<int:article_id>/file/<int:file_id>/makegalley/",
        views.article_file_make_galley,
        name="article_file_make_galley",
    ),
    path("note/<int:article_id>/new/", views.new_note, name="article_new_note"),
    # Publication
    path("publish/", views.publish, name="publish"),
    path(
        "publish/article/<int:article_id>/",
        views.publish_article,
        name="publish_article",
    ),
    path(
        "publish/article/<int:article_id>/check/",
        views.publish_article_check,
        name="publish_article_check",
    ),
    # Issues
    path("manage/issues/", views.manage_issues, name="manage_issues"),
    path(
        "manage/issues/display/",
        views.manage_issue_display,
        name="manage_issue_display",
    ),
    path("manage/issues/order/", views.issue_order, name="issue_order"),
    path(
        "manage/issues/<int:issue_id>/",
        views.manage_issues,
        name="manage_issues_id",
    ),
    path(
        "manage/issues/<int:issue_id>/add/article/",
        views.issue_add_article,
        name="issue_add_article",
    ),
    path(
        "manage/issues/<int:issue_id>/galley/",
        views.issue_galley,
        name="issue_galley",
    ),
    path(
        "manage/issues/<int:issue_id>/order/",
        views.issue_article_order,
        name="issue_article_order",
    ),
    path(
        "manage/issues/<int:issue_id>/editors/",
        views.add_guest_editor,
        name="manage_add_guest_editor",
    ),
    path(
        "manage/issues/<int:issue_id>/editors/remove/",
        views.remove_issue_editor,
        name="manage_remove_issue_editor",
    ),
    re_path(
        r"^manage/issues/(?P<issue_id>\d+)/(?P<event>[-\w.]+)/$",
        views.manage_issues,
        name="manage_issues_event",
    ),
    path(
        "manage/issues/<int:issue_id>/sort/sections/",
        views.sort_issue_sections,
        name="manage_sort_issue_sections",
    ),
    # Article Archive
    path(
        "manage/archive/",
        views.published_article_archive,
        name="manage_archive",
    ),
    path(
        "manage/archive/rejected-archived/",
        views.rejected_archived_article_archive,
        name="manage_rejected_archived_archive",
    ),
    path(
        "manage/archive/article/<int:article_id>/",
        views.manage_archive_article,
        name="manage_archive_article",
    ),
    path(
        "manage/article/<int:article_id>/log/",
        views.manage_article_log,
        name="manage_article_log",
    ),
    path(
        "manage/article/<int:article_id>/log/<int:log_id>/resend/",
        views.resend_logged_email,
        name="manage_resend_logged_email",
    ),
    path(
        "manage/articles/schedule/",
        views.publication_schedule,
        name="publication_schedule",
    ),
    # Languages
    path("manage/languages/", views.manage_languages, name="manage_languages"),
    # Reviewer
    path("reviewer/", views.become_reviewer, name="become_reviewer"),
    # Contact
    path("contact/", views.contact, name="contact"),
    path(
        "contact/recipient/<int:contact_person_id>/",
        views.contact,
        name="journal_contact_with_recipient",
    ),
    # Accessibility
    path("accessibility/", views.accessibility, name="accessibility"),
    # Editorial team
    path("editorialteam/", views.editorial_team, name="editorial_team"),
    # Editorial team
    path(
        "editorialteam/<int:group_id>/",
        views.editorial_team,
        name="editorial_team_group",
    ),
    # Authors page
    path("authors/", views.author_list, name="authors"),
    # Search
    path("search/", views.search, name="search"),
    path("keywords/", views.keywords, name="keywords"),
    path("keywords/<int:keyword_id>/", views.keyword, name="keyword"),
    # Submissions
    path("submissions/", views.submissions, name="journal_submissions"),
    # Download supplementary file
    re_path(
        r"^download/article/(?P<article_id>\d+)/supp_file/(?P<supp_file_id>\d+)/",
        views.download_supp_file,
        name="article_download_supp_file",
    ),
    # Backup DOI patterns, redirect to pubid/id url of article
    re_path(
        r"^article/(?P<identifier_type>doi)/(?P<identifier>{0})/print/$"
        "".format(DOI_REGEX_PATTERN),
        views.doi_redirect,
        name="print_doi_redirect",
    ),
    path("email/user/<int:user_id>/", views.send_user_email, name="send_user_email"),
    path(
        "email/user/<int:user_id>/article/<int:article_id>/",
        views.send_user_email,
        name="send_user_email_article",
    ),
    # Manage users
    path(
        "user/all/",
        views.JournalUsers.as_view(),
        name="journal_users",
    ),
]
