from django.conf.urls import url

from comms import views

urlpatterns = [
    url(r'^$', views.news_list, name='core_news_list'),
    url(r'^tag/(?P<tag>.*)/$', views.news_list, name='core_news_list_tag'),
    url(r'^(?P<presswide>all)/$', views.news_list, name='core_news_list_presswide'),
    url(r'^(?P<presswide>all)/tag/(?P<tag>.*)/$', views.news_list, name='core_news_list_tag_presswide'),
    url(r'^press_overview/$', views.press_overview, name='core_news_press_overview'),

    url(r'^manager/$', views.news, name='core_manager_news'),
    url(r'^manager/edit/(?P<news_pk>\d+)/$', views.edit_news, name='core_manager_edit_news'),

    url(r'^(?P<news_pk>\d+)/$', views.news_item, name='core_news_item'),

    url(r'^(?P<identifier_type>.+?)/(?P<identifier>.+)/image/(?P<file_id>\d+|None)/$',
        views.serve_news_file, name='news_file_download'),
]
