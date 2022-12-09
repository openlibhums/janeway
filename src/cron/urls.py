__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
from django.urls import re_path

from cron import views

urlpatterns = [
    re_path(r'^$', views.home, name='cron_home'),
    re_path(r'^reminders/$', views.reminders_index, name='cron_reminders'),
    re_path(r'^reminders/new/$', views.manage_reminder, name='cron_create_reminder'),
    re_path(r'^reminders/(?P<reminder_id>\d+)/$', views.manage_reminder, name='cron_reminder'),
    re_path(r'^reminders/(?P<reminder_id>\d+)/template/(?P<template_name>.*)/$', views.create_template,
        name='cron_create_template'),

    re_path(r'^readers/$', views.readers_index, name='cron_readers'),
]
