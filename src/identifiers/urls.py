__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
from django.conf.urls import url

from identifiers import views

urlpatterns = [
    url(r'^pingback$', views.pingback, name='crossref_pingback')
]
