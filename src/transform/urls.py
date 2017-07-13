__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
from django.conf.urls import url

from transform import views

urlpatterns = [
    url(r'^galley/(?P<galley_id>.+?)/generate-pdf/$', views.cassius_generate,
        name='cassius_generate'),

    url(r'^galley/(?P<galley_id>.+?)/generate-epub/$', views.epub_generate,
        name='epub_generate'),
]
