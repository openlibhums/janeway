__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django.conf.urls import url

from reports import views


urlpatterns = [

    # Editor URLs
    url(r'^$', views.index, name='reports_index'),
    url(r'^metrics/$', views.metrics, name='reports_metrics'),
    url(r'^doiresolution/$', views.dois, name='reports_dois'),

]
