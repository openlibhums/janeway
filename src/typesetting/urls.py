from django.urls import re_path

from typesetting import views

urlpatterns = [
    re_path(r'^manager/$',
        views.typesetting_manager,
        name='typesetting_manager'
        ),
    re_path(r'^$',
        views.typesetting_articles,
        name='typesetting_articles'
        ),
    re_path(r'^article/(?P<article_id>\d+)/makegalley/file/(?P<file_id>\d+)/$', views.article_file_make_galley,
        name='typesetting_article_file_make_galley'),
    re_path(r'^article/(?P<article_id>\d+)/$',
        views.typesetting_article,
        name='typesetting_article'
        ),
    re_path(r'^article/(?P<article_id>\d+)/typesetter/(?P<assignment_id>\d+)/review/$',
        views.typesetting_review_assignment,
        name='typesetting_review_assignment'
        ),
    re_path(r'^article/(?P<article_id>\d+)/action/(?P<action>claim|unclaim)$',
        views.typesetting_claim_article,
        name='typesetting_claim_article'
        ),
    re_path(r'^article/(?P<article_id>\d+)/galley/(?P<galley_id>\d+)/edit/$',
        views.typesetting_edit_galley,
        name='typesetting_edit_galley'
        ),
    re_path(r'^article/(?P<article_id>\d+)/galley/upload/$',
        views.typesetting_upload_galley,
        name='typesetting_upload_galley'
        ),
    re_path(r'^correction/(?P<correction_id>\d+)/delete/$',
        views.typesetting_delete_correction,
        name='typesetting_delete_correction',
        ),
    re_path(r'^article/(?P<article_id>\d+)/galley/upload/$',
        views.typesetting_upload_galley,
        name='typesetting_upload_galley'
        ),
    re_path(r'^article/(?P<article_id>\d+)/assign/typesetter/$',
        views.typesetting_assign_typesetter,
        name='typesetting_assign_typesetter'
        ),
    re_path(r'^article/(?P<article_id>\d+)/typesetter/(?P<assignment_id>\d+)/notify/$',
        views.typesetting_notify_typesetter,
        name='typesetting_notify_typesetter'
        ),

    re_path(r'^assignments/$',
        views.typesetting_assignments,
        name='typesetting_assignments'
        ),

    re_path(r'^assignments/typesetting/(?P<assignment_id>\d+)/$',
        views.typesetting_assignment,
        name='typesetting_assignment'
        ),
    re_path(r'^assignments/typesetting/(?P<assignment_id>\d+)/download/(?P<file_id>\d+)/$',
        views.typesetting_typesetter_download_file,
        name='typesetting_typesetter_download_file'
        ),
    re_path(r'^article/(?P<article_id>\d+)/assignment/(?P<assignment_id>\d+)/galley/upload/$',
        views.typesetting_upload_galley,
        name='typesetting_assignment_upload_galley'
        ),

    re_path(r'^article/(?P<article_id>\d+)/assign/proofreader/$',
        views.typesetting_assign_proofreader,
        name='typesetting_assign_proofreader'
        ),
    re_path(r'^article/(?P<article_id>\d+)/assign/proofreader/(?P<assignment_id>\d+)/notify/$',
        views.typesetting_notify_proofreader,
        name='typesetting_notify_proofreader'
        ),
    re_path(r'^article/(?P<article_id>\d+)/proofreader/(?P<assignment_id>\d+)/review/$',
        views.typesetting_manage_proofing_assignment,
        name='typesetting_manage_proofing_assignment'
        ),
    re_path(r'^assignments/proofreading/$',
        views.typesetting_proofreading_assignments,
        name='typesetting_proofreading_assignments'
        ),
    re_path(r'^assignments/proofreading/(?P<assignment_id>\d+)/$',
        views.typesetting_proofreading_assignment,
        name='typesetting_proofreading_assignment'
        ),

    re_path(r'^preview_galley/article/(?P<article_id>\d+)/galley/(?P<galley_id>\d+)/assignment/(?P<assignment_id>\d+)/$',
        views.typesetting_preview_galley,
        name='typesetting_preview_galley'
        ),
    re_path(r'^preview_galley/article/(?P<article_id>\d+)/galley/(?P<galley_id>\d+)/$',
        views.typesetting_preview_galley,
        name='editor_preview_galley'
        ),

    re_path(r'^preview/article/(?P<article_id>\d+)/assignment/(?P<assignment_id>\d+)/file/(?P<file_id>\d+)/$',
        views.typesetting_proofing_download,
        name='typesetting_proofing_download'
        ),
    re_path(r'^preview_galley/article/(?P<article_id>\d+)/galley/(?P<galley_id>\d+)/assignment/(?P<assignment_id>\d+)/figures/(?P<file_name>.*)$',
        views.preview_figure,
        name='proofreader_preview_figure'
        ),
    re_path(r'^preview_galley/article/(?P<article_id>\d+)/galley/(?P<galley_id>\d+)/assignment/(?P<assignment_id>\d+)/(?P<file_name>.*)$',
        views.preview_figure,
        name='proofreader_preview_figure_b'
        ),

    re_path(r'^preview_galley/article/(?P<article_id>\d+)/galley/(?P<galley_id>\d+)/figures/(?P<file_name>.*)$',
        views.preview_figure,
        name='typesetter_preview_figure'
        ),
    re_path(r'^preview_galley/article/(?P<article_id>\d+)/galley/(?P<galley_id>\d+)/(?P<file_name>.*)$',
        views.preview_figure,
        name='typesetter_preview_figure_b'
        ),

    re_path(r'^article/(?P<article_id>\d+)/file/(?P<file_id>\d+)/download/$',
        views.typesetting_download_file,
        name='typesetting_download_file'
        ),

    re_path(r'^galley/(?P<galley_id>\d+)/delete/$',
        views.typesetting_delete_galley,
        name='typesetting_delete_galley'
        ),
    re_path(r'^supp-file/(?P<supp_file_id>\d+)/doi/$',
        views.mint_supp_doi,
        name='typesetting_mint_supp_doi'
        ),
]
