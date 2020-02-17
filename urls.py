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
    url(r'^article/(?P<article_id>\d+)/typesetter/assign/$',
        views.typesetting_assign_typesetter,
        name='typesetting_assign_typesetter'
        ),
    url(r'^article/(?P<article_id>\d+)/typesetter/(?P<assignment_id>\d+)/notify/$',
        views.typesetting_notify_typesetter,
        name='typesetting_notify_typesetter'
        ),
]
