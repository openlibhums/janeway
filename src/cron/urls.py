__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
from django.conf.urls import url

from cron import views

urlpatterns = [
    url(r'^$', views.home, name='cron_home'),
    url(r'^reminders/$', views.reminders_index, name='cron_reminders'),
    url(r'^reminders/new/$', views.manage_reminder, name='cron_create_reminder'),
    url(r'^reminders/(?P<reminder_id>\d+)/$', views.manage_reminder, name='cron_reminder'),
    url(r'^reminders/(?P<reminder_id>\d+)/template/(?P<template_name>.*)/$', views.create_template,
        name='cron_create_template'),
]
