__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.urls import re_path

from journal import views
from identifiers.models import NON_DOI_IDENTIFIER_TYPES, DOI_REGEX_PATTERN

NON_DOI_PIPE_SEPARATED_IDENTIFIERS = "|".join(NON_DOI_IDENTIFIER_TYPES)

# Various url patterns in this module have duplicated names
# This is so we can handle DOI patterns using a more restrictive
# Regex pattern an example is this is 'article_view'

urlpatterns = [
    # Figures and download patterns
    re_path(r'^article/(?P<identifier_type>{0})/(?P<identifier>[\w.-]+)/print/$'
        ''.format(NON_DOI_PIPE_SEPARATED_IDENTIFIERS),
        views.print_article,
        name='article_print_article'),
    re_path(r'^article/(?P<article_id>\d+)/galley/(?P<galley_id>\d+)/figure/(?P<file_name>.*)/$',
        views.article_figure,
        name='article_galley_figure'),
    re_path(r'^article/(?P<identifier_type>id)/(?P<identifier>.+)/file/(?P<file_id>\d+)/replace$',
        views.replace_article_file,
        name='article_file_replace'),
    re_path(r'^article/(?P<identifier_type>id)/(?P<identifier>.+)/file/(?P<file_id>\d+|None)/$',
        views.serve_article_file,
        name='article_file_download'),
    re_path(r'^article/(?P<identifier_type>id)/(?P<identifier>.+)/file_history/(?P<file_id>\d+|None)/$',
        views.serve_article_file_history,
        name='article_file_history_download'),
    re_path(r'^article/(?P<article_id>\d+)/galley/(?P<galley_id>\d+)/download/',
        views.download_galley,
        name='article_download_galley'),
    re_path(r'^article/(?P<article_id>\d+)/galley/(?P<galley_id>\d+)/view/',
        views.view_galley,
        name='article_view_galley'),
    re_path(r'^article/(?P<identifier_type>id)/(?P<identifier>.+)/download/pdf/$',
        views.serve_article_pdf,
        name='serve_article_pdf'),
    re_path(r'^article/(?P<identifier_type>id)/(?P<identifier>.+)/download/xml/$',
        views.serve_article_xml,
        name='serve_article_xml'),
    re_path(r'^article/(?P<identifier_type>id)/(?P<identifier>.+)/download/ris/$',
        views.serve_article_ris,
        name='serve_article_ris'),
    re_path(r'^article/(?P<identifier_type>id)/(?P<identifier>.+)/download/bib/$',
        views.serve_article_bib,
        name='serve_article_bib'),
    re_path(r'^article/(?P<identifier_type>{0})/(?P<identifier>[\w.-]+)/table/(?P<table_name>.+)$'
        ''.format(NON_DOI_PIPE_SEPARATED_IDENTIFIERS),
        views.download_table,
        name='article_table'),
    re_path(r'^article/(?P<identifier_type>{0})/(?P<identifier>[\w.-]+)/(?P<file_name>.+)$'
        ''.format(NON_DOI_PIPE_SEPARATED_IDENTIFIERS),
        views.identifier_figure,
        name='article_figure'),

    re_path(
        r'^articles/$',
        views.PublishedArticlesListView.as_view(),
        name='journal_articles',
    ),

    re_path(r'^funder_articles/(?P<funder_id>.+)$', views.funder_articles, name='funder_articles'),

    # Issues/Collections
    re_path(r'^issues/$', views.issues, name='journal_issues'),
    re_path(r'^issue/current/$', views.current_issue, name='current_issue'),
    re_path(r'^issue/(?P<issue_id>\d+)/info/$', views.issue, name='journal_issue'),
    re_path(r'^issue/(?P<issue_id>\d+)/download/(?P<galley_id>\d+)$',
        views.download_issue_galley,
        name='journal_issue_download_galley'),
    re_path(r'^collections/$', views.collections, name='journal_collections_type'),
    re_path(r'^collections/(?P<collection_id>\d+)/$', views.collection, name='journal_collection'),

    # The URLS below are roughly equivalent but we need both because of backwards compatibility reasons
    re_path(r'^collections/(?P<issue_type_code>[a-zA-Z-_]+)/$', views.collections, name='journal_collections'),
    re_path(r'^collections/type/(?P<issue_type_code>[\da-zA-Z-_]+)/$', views.collections, name='journal_collections_with_digits'),
    # The URLS below are roughly equivalent but we need both because of backwards compatibility reasons
    re_path(r'^collection/(?P<collection_code>[a-zA-Z-_]+)/$', views.collection_by_code, name='journal_collection_by_code'),
    re_path(r'^collection/code/(?P<collection_code>[\da-zA-Z-_]+)/$', views.collection_by_code, name='journal_collection_by_code_with_digits'),

    re_path(r'^cover/$', views.serve_journal_cover, name='journal_cover_download'),
    re_path(r'^volume/(?P<volume_number>\d+)/issue/(?P<issue_number>\d+)/$', views.volume, name='journal_volume'),

    # Article patterns
    re_path(r'^article/(?P<identifier_type>{0})/(?P<identifier>[\w.-]+)/edit/$'
        ''.format(NON_DOI_PIPE_SEPARATED_IDENTIFIERS),
        views.edit_article,
        name='article_edit'),
    re_path(r'^article/(?P<identifier_type>{0})/(?P<identifier>[\w.-]+)/$'
        ''.format(NON_DOI_PIPE_SEPARATED_IDENTIFIERS),
        views.article,
        name='article_view'
        ),
    re_path(r'^article/(?P<identifier_type>doi)/(?P<identifier>{0})/$'
        ''.format(DOI_REGEX_PATTERN),
        views.doi_redirect,
        name='doi_redirect'),
    re_path(r'^article/(?P<identifier_type>[\w.-_]+)/(?P<identifier>[\w.-]+)/$',
        views.article_from_identifier,
        name='article_view_custom_identifier',
        ),


    # File management
    re_path(r'^(?P<article_id>\d+)/files/management/$', views.document_management,
        name='document_management'),
    re_path(r'^(?P<article_id>\d+)/files/(?P<file_id>\d+)/info/$', views.submit_files_info,
        name='submit_replacement_files_info'),
    re_path(r'^(?P<article_id>\d+)/files/(?P<file_id>\d+)/history/$', views.file_history,
        name='file_history'),
    re_path(r'^(?P<article_id>\d+)/files/(?P<file_id>\d+)/delete/$', views.file_delete,
        name='file_delete'),
    re_path(r'^(?P<article_id>\d+)/files/(?P<file_id>\d+)/old/(?P<file_history_id>\d+)/reinstate/$',
        views.file_reinstate,
        name='file_reinstate'),
    re_path(r'^(?P<article_id>\d+)/file/(?P<file_id>\d+)/makegalley/$', views.article_file_make_galley,
        name='article_file_make_galley'),
    re_path(r'^note/(?P<article_id>\d+)/new/$', views.new_note, name='article_new_note'),

    # Publication
    re_path(r'^publish/$',
        views.publish, name='publish'),
    re_path(r'^publish/article/(?P<article_id>\d+)/$',
        views.publish_article, name='publish_article'),
    re_path(r'^publish/article/(?P<article_id>\d+)/check/$',
        views.publish_article_check, name='publish_article_check'),

    # Issues
    re_path(r'^manage/issues/$',
        views.manage_issues, name='manage_issues'),
    re_path(r'^manage/issues/display/$',
        views.manage_issue_display, name='manage_issue_display'),
    re_path(r'^manage/issues/order/$',
        views.issue_order, name='issue_order'),
    re_path(r'^manage/issues/(?P<issue_id>\d+)/$',
        views.manage_issues, name='manage_issues_id'),
    re_path(r'^manage/issues/(?P<issue_id>\d+)/add/article/$',
        views.issue_add_article, name='issue_add_article'),
    re_path(r'^manage/issues/(?P<issue_id>\d+)/galley/$',
        views.issue_galley, name='issue_galley'),
    re_path(r'^manage/issues/(?P<issue_id>\d+)/order/$',
        views.issue_article_order, name='issue_article_order'),
    re_path(r'^manage/issues/(?P<issue_id>\d+)/editors/$',
        views.add_guest_editor, name='manage_add_guest_editor'),
    re_path(r'^manage/issues/(?P<issue_id>\d+)/editors/remove/$',
        views.remove_issue_editor, name='manage_remove_issue_editor'),
    re_path(r'^manage/issues/(?P<issue_id>\d+)/(?P<event>[-\w.]+)/$',
        views.manage_issues, name='manage_issues_event'),
    re_path(r'^manage/issues/(?P<issue_id>\d+)/sort/sections/$',
        views.sort_issue_sections, name='manage_sort_issue_sections'),

    # Article Archive
    re_path(r'^manage/archive/$',
        views.manage_archive, name='manage_archive'),
    re_path(r'^manage/archive/article/(?P<article_id>\d+)/$',
        views.manage_archive_article, name='manage_archive_article'),

    re_path(r'^manage/article/(?P<article_id>\d+)/log/$',
        views.manage_article_log, name='manage_article_log'),

    re_path(r'^manage/article/(?P<article_id>\d+)/log/(?P<log_id>\d+)/resend/$',
        views.resend_logged_email, name='manage_resend_logged_email'),

    re_path(r'^manage/articles/schedule/$',
        views.publication_schedule, name='publication_schedule'),

    # Languages
    re_path(r'^manage/languages/$',
        views.manage_languages, name='manage_languages'),

    # Reviewer
    re_path(r'^reviewer/$',
        views.become_reviewer, name='become_reviewer'),
    # Contact
    re_path(r'^contact/$',
        views.contact, name='contact'),
    # Editorial team
    re_path(r'^editorialteam/$',
        views.editorial_team, name='editorial_team'),
    # Editorial team
    re_path(r'^editorialteam/(?P<group_id>\d+)/$',
        views.editorial_team, name='editorial_team_group'),
    # Authors page
    re_path(r'^authors/$',
        views.author_list, name='authors'),

    # Search
    re_path(r'^search/$',
        views.search, name='search'),
    re_path(r'^keywords/$',
        views.keywords, name='keywords'),

    re_path(r'^keywords/(?P<keyword_id>\d+)/$',
        views.keyword, name='keyword'),

    # Submissions
    re_path(r'^submissions/$',
        views.submissions, name='journal_submissions'),

    # Edit file with Texture
    re_path(r'^texture/(?P<file_id>\d+)/edit/$',
        views.texture_edit, name='texture_edit'),

    # Download supplementary file
    re_path(r'^download/article/(?P<article_id>\d+)/supp_file/(?P<supp_file_id>\d+)/',
        views.download_supp_file,
        name='article_download_supp_file'),

    # Backup DOI patterns, redirect to pubid/id url of article
    re_path(r'^article/(?P<identifier_type>doi)/(?P<identifier>{0})/print/$'
        ''.format(DOI_REGEX_PATTERN),
        views.doi_redirect,
        name='print_doi_redirect'),


    re_path(r'^email/user/(?P<user_id>\d+)/$',
        views.send_user_email, name='send_user_email'),
    re_path(r'^email/user/(?P<user_id>\d+)/article/(?P<article_id>\d+)/$',
        views.send_user_email, name='send_user_email_article'),

]
