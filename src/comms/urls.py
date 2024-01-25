from django.urls import re_path

from comms import views

urlpatterns = [
    re_path(r'^$', views.news_list, name='core_news_list'),
    re_path(r'^tag/(?P<tag>.*)/$', views.news_list, name='core_news_list_tag'),
    re_path(
        r'^(?P<presswide>all)/$',
        views.news_list,
        name='core_news_list_presswide',
    ),
    re_path(
        r'^(?P<presswide>all)/tag/(?P<tag>.*)/$',
        views.news_list,
        name='core_news_list_tag_presswide',
    ),
    re_path(r'^manager/$', views.news, name='core_manager_news'),
    re_path(r'^manager/edit/(?P<news_pk>\d+)/$', views.edit_news, name='core_manager_edit_news'),

    re_path(r'^(?P<news_pk>\d+)/$', views.news_item, name='core_news_item'),

    re_path(r'^(?P<identifier_type>.+?)/(?P<identifier>.+)/image/(?P<file_id>\d+|None)/$',
        views.serve_news_file, name='news_file_download'),
]
