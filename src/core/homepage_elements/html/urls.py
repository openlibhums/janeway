__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.conf.urls import url
from core.homepage_elements.html import views

urlpatterns = [
    # Featured Articles
    url(r'^$', views.html_settings, name='html_settings'),
]
