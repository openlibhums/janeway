__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
from django.urls import path

from install import views

urlpatterns = [
    path("", views.index, name="install_index"),
    path("journal/", views.journal, name="install_journal"),
    path("next/", views.next, name="install_next"),
]
