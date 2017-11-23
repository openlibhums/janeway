__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django.conf.urls import url

from utils import views


urlpatterns = [

    # Editor URLs
    url(r'^mailgun_webhook', views.mailgun_webhook, name='mailgun_webhook'),

]
