__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django.urls import path

from reports import views


urlpatterns = [
    # Editor URLs
    path("", views.index, name="reports_index"),
    path("metrics/", views.metrics, name="reports_metrics"),
    path("doiresolution/", views.dois, name="reports_dois"),
]
