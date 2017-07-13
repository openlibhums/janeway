__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
from django.conf.urls import url

from metrics import views

urlpatterns = [

    url(r'^sushi/$',
        views.sushi,
        name='sushi'),

    # NB to avoid denial of service attacks, we do not allow requests to customize the date range
    url(r'^counter/reports/jr1/(?P<output_format>.+)/$',
        views.jr_one_no_date,
        name='journal_report_one_no_date'),

    url(r'^counter/reports/jr1_goa/(?P<output_format>.+)/$',
        views.jr_one_goa_no_date,
        name='journal_report_one_goa_no_date'),

    url(r'^counter/reports/jr2/(?P<output_format>.+)/$',
        views.jr_two_no_date,
        name='journal_report_two_no_date')

]
