__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.conf.urls import url

from journal import views

urlpatterns = [
    # Probably needs some multi-journal logic here
    url(r'^article/(?P<article_id>\d+)/galley/(?P<galley_id>\d+)/figure/(?P<file_name>.*)/$',
        views.article_figure,
        name='article_figure'),
    url(r'^article/(?P<identifier_type>.+?)/(?P<identifier>.+)/file/(?P<file_id>\d+)/replace$',
        views.replace_article_file,
        name='article_file_replace'),
    url(r'^article/(?P<identifier_type>.+?)/(?P<identifier>.+)/file/(?P<file_id>\d+|None)/$',
        views.serve_article_file,
        name='article_file_download'),
    url(r'^article/(?P<article_id>\d+)/galley/(?P<galley_id>\d+)/download/',
        views.download_galley,
        name='article_download_galley'),
    url(r'^article/(?P<article_id>\d+)/galley/(?P<galley_id>\d+)/view/',
        views.view_galley,
        name='article_view_galley'),
    url(r'^article/(?P<identifier_type>.+?)/(?P<identifier>.+?/.+?)/table/(?P<table_name>.+)$',
        views.download_table,
        name='article_figure'),
    url(r'^article/(?P<identifier_type>.+?)/(?P<identifier>.+?/.+?)/(?P<file_name>.+)$',
        views.identifier_figure,
        name='article_figure'),

    url(r'^articles/$', views.articles, name='journal_articles'),

    url(r'^issues/$', views.issues, name='journal_issues'),
    url(r'^issue/current/$', views.current_issue, name='current_issue'),
    url(r'^issue/(?P<issue_id>\d+)/info/$', views.issue, name='journal_issue'),
    url(r'^issue/(?P<issue_id>\d+)/download/$', views.download_issue, name='journal_issue_download'),
    url(r'^collections/$', views.collections, name='journal_collections'),
    url(r'^collections/(?P<collection_id>\d+)/$', views.collection, name='journal_collection'),
    url(r'^cover/$', views.serve_journal_cover, name='journal_cover_download'),

    url(r'^article/(?P<identifier_type>.+?)/(?P<identifier>.+)/edit/$', views.edit_article, name='article_edit'),
    url(r'^article/(?P<identifier_type>.+?)/(?P<identifier>.+)/print/$', views.print_article,
        name='article_print_article'),
    url(r'^article/(?P<identifier_type>.+?)/(?P<identifier>.+)/$', views.article, name='article_view'),

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
    url(r'^manage/issues/order/$',
        views.issue_order, name='issue_order'),
    url(r'^manage/issues/(?P<issue_id>\d+)/$',
        views.manage_issues, name='manage_issues_id'),
    url(r'^manage/issues/(?P<issue_id>\d+)/add/article/$',
        views.issue_add_article, name='issue_add_article'),
    url(r'^manage/issues/(?P<issue_id>\d+)/order/$',
        views.issue_article_order, name='issue_article_order'),
    url(r'^manage/issues/(?P<issue_id>\d+)/guest/$',
        views.add_guest_editor, name='manage_add_guest_editor'),
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

    # Search
    url(r'^search/$',
        views.search, name='search'),

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

]
