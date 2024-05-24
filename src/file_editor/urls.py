from django.urls import re_path

from file_editor import views
from journal.views import article_figure

urlpatterns = [
    re_path(r'^$', views.galley_list, name='editors_galley_list'),
    re_path(
        r'^edit/article/(?P<article_id>\d+)/galley/(?P<galley_id>\d+)/$',
        views.edit_galley_file,
        name='editors_edit_galley_file',
    ),
    re_path(
        r'^edit/article/(?P<article_id>\d+)/galley/(?P<galley_id>\d+)/figure/(?P<file_name>.*)$',
        article_figure,
        name='editors_article_galley_figure'
    ),
    re_path(
        r'^edit/article/(?P<article_id>\d+)/galley/(?P<galley_id>\d+)/(?P<file_name>.*)$',
        article_figure,
        name='editors_article_galley_figure'
    ),
]