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


]
