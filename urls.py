from django.conf.urls import url

from plugins.typesetting import views

urlpatterns = [
    url(r'^manager/$',
        views.typesetting_manager,
        name='typesetting_manager'
        ),
    url(r'^$',
        views.typesetting_articles,
        name='typesetting_articles'
        ),
    url(r'^article/(?P<article_id>\d+)/$',
        views.typesetting_article,
        name='typesetting_article'
        ),
    url(r'^article/(?P<article_id>\d+)/typesetter/(?P<assignment_id>\d+)/review/$',
        views.typesetting_review_assignment,
        name='typesetting_review_assignment'
        ),
    url(r'^article/(?P<article_id>\d+)/action/(?P<action>claim|unclaim)$',
        views.typesetting_claim_article,
        name='typesetting_claim_article'
        ),
    url(r'^article/(?P<article_id>\d+)/galley/(?P<galley_id>\d+)/edit/$',
        views.typesetting_edit_galley,
        name='typesetting_edit_galley'
        ),
    url(r'^article/(?P<article_id>\d+)/galley/upload/$',
        views.typesetting_upload_galley,
        name='typesetting_upload_galley'
        ),
    url(r'^article/(?P<article_id>\d+)/assign/typesetter/$',
        views.typesetting_assign_typesetter,
        name='typesetting_assign_typesetter'
        ),
    url(r'^article/(?P<article_id>\d+)/typesetter/(?P<assignment_id>\d+)/notify/$',
        views.typesetting_notify_typesetter,
        name='typesetting_notify_typesetter'
        ),

    url(r'^assignments/$',
        views.typesetting_assignments,
        name='typesetting_assignments'
        ),

    url(r'^assignments/typesetting/(?P<assignment_id>\d+)/$',
        views.typesetting_assignment,
        name='typesetting_assignment'
        ),
    url(r'^assignments/typesetting/(?P<assignment_id>\d+)/download/(?P<file_id>\d+)/$',
        views.typesetting_typesetter_download_file,
        name='typesetting_typesetter_download_file'
        ),
    url(r'^article/(?P<article_id>\d+)/assignment/(?P<assignment_id>\d+)/galley/upload/$',
        views.typesetting_upload_galley,
        name='typesetting_assignment_upload_galley'
        ),

    url(r'^article/(?P<article_id>\d+)/assign/proofreader/$',
        views.typesetting_assign_proofreader,
        name='typesetting_assign_proofreader'
        ),
    url(r'^article/(?P<article_id>\d+)/assign/proofreader/(?P<assignment_id>\d+)/notify/$',
        views.typesetting_notify_proofreader,
        name='typesetting_notify_proofreader'
        ),
    url(r'^article/(?P<article_id>\d+)/proofreader/(?P<assignment_id>\d+)/review/$',
        views.typesetting_manage_proofing_assignment,
        name='typesetting_manage_proofing_assignment'
        ),
    url(r'^assignments/proofreading/$',
        views.typesetting_proofreading_assignments,
        name='typesetting_proofreading_assignments'
        ),
    url(r'^assignments/proofreading/(?P<assignment_id>\d+)/$',
        views.typesetting_proofreading_assignment,
        name='typesetting_proofreading_assignment'
        ),

    url(r'^preview_galley/(?P<galley_id>\d+)/assignment/(?P<assignment_id>\d+)/$',
        views.typesetting_preview_galley,
        name='typesetting_preview_galley'
        ),
    url(r'^preview_galley/(?P<galley_id>\d+)/article/(?P<article_id>\d+)/$',
        views.typesetting_preview_galley,
        name='editor_preview_galley'
        ),

    url(r'^preview/assignment/(?P<assignment_id>\d+)/file/(?P<file_id>\d+)/$',
        views.typesetting_proofing_download,
        name='typesetting_proofing_download'
        ),
    url(r'^preview_galley/(?P<galley_id>\d+)/assignment/(?P<assignment_id>\d+)/figures/(?P<file_name>.*)$',
        views.preview_figure,
        name='proofreader_preview_figure'
        ),

    url(r'^preview_galley/(?P<galley_id>\d+)/article/(?P<article_id>\d+)/figures/(?P<file_name>.*)$',
        views.preview_figure,
        name='typesetter_preview_figure'
        )
]
