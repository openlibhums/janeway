__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django.conf.urls import url

from preprint import views

urlpatterns = [

    url(r'^$',
        views.preprints_home,
        name='preprints_home'),

    url(r'^about/$',
            views.preprints_about,
            name='preprints_about'),

    url(r'^search/$',
            views.preprints_search,
            name='preprints_search'),

    url(r'^search/(?P<search_term>.*)/$',
        views.preprints_search,
        name='preprints_search_with_term'),

    url(r'^view/(?P<article_id>\d+)/$',
        views.preprints_article,
        name='preprints_article'),

    url(r'^view/(?P<article_id>\d+)/pdf/$',
        views.preprints_pdf,
        name='preprints_pdf'),

    url(r'^list/$',
        views.preprints_list,
        name='preprints_list'),

    url(r'^submit/start/$',
        views.preprints_submit,
        name='preprints_submit'),

    url(r'^submit/(?P<article_id>\d+)/$',
        views.preprints_submit,
        name='preprints_submit_with_id'),

    url(r'^submit/(?P<article_id>\d+)/authors/$',
        views.preprints_authors,
        name='preprints_authors'),

    url(r'^submit/(?P<article_id>\d+)/files/$',
        views.preprints_files,
        name='preprints_files'),

    url(r'^submit/(?P<article_id>\d+)/review/$',
        views.preprints_review,
        name='preprints_review'),

]
