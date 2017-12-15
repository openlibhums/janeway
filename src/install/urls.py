__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
from django.conf.urls import url

from install import views

urlpatterns = [
    url(r'^$', views.index, name='install_index'),
    url(r'^journal/$', views.journal, name='install_journal'),
    url(r'^next/$', views.next, name='install_next')
]
