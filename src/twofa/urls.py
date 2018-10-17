__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
from django.conf.urls import url

from twofa import views

urlpatterns = [
    url(r'^$', views.index, name='twofa_index'),
    url(r'^handler/$', views.handler, name='twofa_handler')
]
