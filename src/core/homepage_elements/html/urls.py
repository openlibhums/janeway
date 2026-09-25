__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.urls import path
from core.homepage_elements.html import views

urlpatterns = [
    # Featured Articles
    path("", views.html_settings, name="html_settings"),
]
