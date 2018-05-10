__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django.contrib import admin
from cron import models


class CronTaskAdmin(admin.ModelAdmin):
    list_display = ('pk', 'task_type', 'run_at', 'article')


class SentReminderAdmin(admin.ModelAdmin):
    list_display = ('type', 'object_id', 'sent')


class ReminderAdmin(admin.ModelAdmin):
    list_display = ('pk', 'journal', 'type', 'run_type', 'days', 'subject')


admin_list = [
    (models.CronTask, CronTaskAdmin),
    (models.Reminder, ReminderAdmin),
    (models.SentReminder, SentReminderAdmin),
]

[admin.site.register(*t) for t in admin_list]
