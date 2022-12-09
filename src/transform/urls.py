__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
from django.urls import re_path

from transform import views

urlpatterns = [
    re_path(r'^galley/(?P<galley_id>.+?)/generate-pdf/$', views.cassius_generate,
        name='cassius_generate'),

    re_path(r'^galley/(?P<galley_id>.+?)/generate-epub/$', views.epub_generate,
        name='epub_generate'),
]
