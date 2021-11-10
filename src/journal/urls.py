__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.conf.urls import url

from journal import views
from identifiers.models import NON_DOI_IDENTIFIER_TYPES, DOI_REGEX_PATTERN

NON_DOI_PIPE_SEPARATED_IDENTIFIERS = "|".join(NON_DOI_IDENTIFIER_TYPES)

# Various url patterns in this module have duplicated names
# This is so we can handle DOI patterns using a more restrictive
# Regex pattern an example is this is 'article_view'

urlpatterns = [
    # Figures and download patterns
    url(r'^article/(?P<identifier_type>{0})/(?P<identifier>[\w.-]+)/print/$'
        ''.format(NON_DOI_PIPE_SEPARATED_IDENTIFIERS),
        views.print_article,
        name='article_print_article'),
    url(r'^article/(?P<article_id>\d+)/galley/(?P<galley_id>\d+)/figure/(?P<file_name>.*)/$',
        views.article_figure,
        name='article_galley_figure'),
    url(r'^article/(?P<identifier_type>id)/(?P<identifier>.+)/file/(?P<file_id>\d+)/replace$',
        views.replace_article_file,
        name='article_file_replace'),
    url(r'^article/(?P<identifier_type>id)/(?P<identifier>.+)/file/(?P<file_id>\d+|None)/$',
        views.serve_article_file,
        name='article_file_download'),
    url(r'^article/(?P<identifier_type>id)/(?P<identifier>.+)/file_history/(?P<file_id>\d+|None)/$',
        views.serve_article_file_history,
        name='article_file_history_download'),
    url(r'^article/(?P<article_id>\d+)/galley/(?P<galley_id>\d+)/download/',
        views.download_galley,
        name='article_download_galley'),
    url(r'^article/(?P<article_id>\d+)/galley/(?P<galley_id>\d+)/view/',
        views.view_galley,
        name='article_view_galley'),
    url(r'^article/(?P<identifier_type>id)/(?P<identifier>.+)/download/xml/$',
        views.serve_article_xml,
        name='serve_article_xml'),
    url(r'^article/(?P<identifier_type>{0})/(?P<identifier>[\w.-]+)/table/(?P<table_name>.+)$'
        ''.format(NON_DOI_PIPE_SEPARATED_IDENTIFIERS),
        views.download_table,
        name='article_table'),
    url(r'^article/(?P<identifier_type>{0})/(?P<identifier>[\w.-]+)/(?P<file_name>.+)$'
        ''.format(NON_DOI_PIPE_SEPARATED_IDENTIFIERS),
        views.identifier_figure,
        name='article_figure'),

    url(r'^articles/$', views.articles, name='journal_articles'),

    url(r'^funder_articles/(?P<funder_id>.+)$', views.funder_articles, name='funder_articles'),

    # Issues/Collections
    url(r'^issues/$', views.issues, name='journal_issues'),
    url(r'^issue/current/$', views.current_issue, name='current_issue'),
    url(r'^issue/(?P<issue_id>\d+)/info/$', views.issue, name='journal_issue'),
    url(r'^issue/(?P<issue_id>\d+)/download/(?P<galley_id>\d+)$',
        views.download_issue_galley,
        name='journal_issue_download_galley'),
    url(r'^article/(?P<article_id>\d+)/galley/(?P<galley_id>\d+)/download/',
        views.download_galley,
        name='article_download_galley'),
    url(r'^collections/$', views.collections, name='journal_collections_type'),
    url(r'^collections/(?P<issue_type_code>[a-zA-Z]+)/$', views.collections, name='journal_collections'),
    url(r'^collections/(?P<collection_id>\d+)/$', views.collection, name='journal_collection'),
    url(r'^cover/$', views.serve_journal_cover, name='journal_cover_download'),
    url(r'^volume/(?P<volume_number>\d+)/issue/(?P<issue_number>\d+)/$', views.volume, name='journal_volume'),

    # Article patterns
    url(r'^article/(?P<identifier_type>{0})/(?P<identifier>[\w.-]+)/edit/$'
        ''.format(NON_DOI_PIPE_SEPARATED_IDENTIFIERS),
        views.edit_article,
        name='article_edit'),
    url(r'^article/(?P<identifier_type>{0})/(?P<identifier>[\w.-]+)/$'
        ''.format(NON_DOI_PIPE_SEPARATED_IDENTIFIERS),
        views.article,
        name='article_view'
        ),
    url(r'^article/(?P<identifier_type>doi)/(?P<identifier>{0})/$'
        ''.format(DOI_REGEX_PATTERN),
        views.doi_redirect,
        name='doi_redirect'),
    url(r'^article/(?P<identifier_type>[\w.-_]+)/(?P<identifier>[\w.-]+)/$',
        views.article_from_identifier,
        name='article_view_custom_identifier',
        ),


    # File management
    url(r'^(?P<article_id>\d+)/files/management/$', views.document_management,
        name='document_management'),
    url(r'^(?P<article_id>\d+)/files/(?P<file_id>\d+)/info/$', views.submit_files_info,
        name='submit_replacement_files_info'),
    url(r'^(?P<article_id>\d+)/files/(?P<file_id>\d+)/history/$', views.file_history,
        name='file_history'),
    url(r'^(?P<article_id>\d+)/files/(?P<file_id>\d+)/delete/$', views.file_delete,
        name='file_delete'),
    url(r'^(?P<article_id>\d+)/files/(?P<file_id>\d+)/old/(?P<file_history_id>\d+)/reinstate/$',
        views.file_reinstate,
        name='file_reinstate'),
    url(r'^(?P<article_id>\d+)/file/(?P<file_id>\d+)/makegalley/$', views.article_file_make_galley,
        name='article_file_make_galley'),
    url(r'^note/(?P<article_id>\d+)/new/$', views.new_note, name='article_new_note'),

    # Publication
    url(r'^publish/$',
        views.publish, name='publish'),
    url(r'^publish/article/(?P<article_id>\d+)/$',
        views.publish_article, name='publish_article'),
    url(r'^publish/article/(?P<article_id>\d+)/check/$',
        views.publish_article_check, name='publish_article_check'),

    # Issues
    url(r'^manage/issues/$',
        views.manage_issues, name='manage_issues'),
    url(r'^manage/issues/display/$',
        views.manage_issue_display, name='manage_issue_display'),
    url(r'^manage/issues/order/$',
        views.issue_order, name='issue_order'),
    url(r'^manage/issues/(?P<issue_id>\d+)/$',
        views.manage_issues, name='manage_issues_id'),
    url(r'^manage/issues/(?P<issue_id>\d+)/add/article/$',
        views.issue_add_article, name='issue_add_article'),
    url(r'^manage/issues/(?P<issue_id>\d+)/galley/$',
        views.issue_galley, name='issue_galley'),
    url(r'^manage/issues/(?P<issue_id>\d+)/order/$',
        views.issue_article_order, name='issue_article_order'),
    url(r'^manage/issues/(?P<issue_id>\d+)/editors/$',
        views.add_guest_editor, name='manage_add_guest_editor'),
    url(r'^manage/issues/(?P<issue_id>\d+)/editors/remove/$',
        views.remove_issue_editor, name='manage_remove_issue_editor'),
    url(r'^manage/issues/(?P<issue_id>\d+)/(?P<event>[-\w.]+)/$',
        views.manage_issues, name='manage_issues_event'),
    url(r'^manage/issues/(?P<issue_id>\d+)/sort/sections/$',
        views.sort_issue_sections, name='manage_sort_issue_sections'),

    # Article Archive
    url(r'^manage/archive/$',
        views.manage_archive, name='manage_archive'),
    url(r'^manage/archive/article/(?P<article_id>\d+)/$',
        views.manage_archive_article, name='manage_archive_article'),

    url(r'^manage/article/(?P<article_id>\d+)/log/$',
        views.manage_article_log, name='manage_article_log'),

    url(r'^manage/article/(?P<article_id>\d+)/log/(?P<log_id>\d+)/resend/$',
        views.resend_logged_email, name='manage_resend_logged_email'),

    url(r'^manage/articles/schedule/$',
        views.publication_schedule, name='publication_schedule'),

    # Reviewer
    url(r'^reviewer/$',
        views.become_reviewer, name='become_reviewer'),
    # Contact
    url(r'^contact/$',
        views.contact, name='contact'),
    # Editorial team
    url(r'^editorialteam/$',
        views.editorial_team, name='editorial_team'),
    # Editorial team
    url(r'^editorialteam/(?P<group_id>\d+)/$',
        views.editorial_team, name='editorial_team_group'),
    # Authors page
    url(r'^authors/$',
        views.author_list, name='authors'),

    # Search
    url(r'^search/$',
        views.search, name='search'),
    url(r'^keywords/$',
        views.keywords, name='keywords'),

    url(r'^keywords/(?P<keyword_id>\d+)/$',
        views.keyword, name='keyword'),

    # Submissions
    url(r'^submissions/$',
        views.submissions, name='journal_submissions'),

    # Edit file with Texture
    url(r'^texture/(?P<file_id>\d+)/edit/$',
        views.texture_edit, name='texture_edit'),

    # Download supplementary file
    url(r'^download/article/(?P<article_id>\d+)/supp_file/(?P<supp_file_id>\d+)/',
        views.download_supp_file,
        name='article_download_supp_file'),

    # Backup DOI patterns, redirect to pubid/id url of article
    url(r'^article/(?P<identifier_type>doi)/(?P<identifier>{0})/print/$'
        ''.format(DOI_REGEX_PATTERN),
        views.doi_redirect,
        name='print_doi_redirect'),


    url(r'^email/user/(?P<user_id>\d+)/$',
        views.send_user_email, name='send_user_email'),
    url(r'^email/user/(?P<user_id>\d+)/article/(?P<article_id>\d+)/$',
        views.send_user_email, name='send_user_email_article'),

]
