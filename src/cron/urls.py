__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
from django.urls import path
from django.urls import re_path

from cron import views

urlpatterns = [
    path("", views.home, name="cron_home"),
    path("reminders/", views.reminders_index, name="cron_reminders"),
    path("reminders/new/", views.manage_reminder, name="cron_create_reminder"),
    path(
        "reminders/<int:reminder_id>/",
        views.manage_reminder,
        name="cron_reminder",
    ),
    re_path(
        r"^reminders/(?P<reminder_id>\d+)/template/(?P<template_name>.*)/$",
        views.create_template,
        name="cron_create_template",
    ),
    path("readers/", views.readers_index, name="cron_readers"),
]
