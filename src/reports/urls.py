__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django.urls import re_path

from reports import views


urlpatterns = [

    # Editor URLs
    re_path(r'^$', views.index, name='reports_index'),
    re_path(r'^metrics/$', views.metrics, name='reports_metrics'),
    re_path(r'^doiresolution/$', views.dois, name='reports_dois'),

]
