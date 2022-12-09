__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
from django.urls import re_path

from install import views

urlpatterns = [
    re_path(r'^$', views.index, name='install_index'),
    re_path(r'^journal/$', views.journal, name='install_journal'),
    re_path(r'^next/$', views.next, name='install_next')
]
