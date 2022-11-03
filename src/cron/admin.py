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
    list_filter = ('type', 'sent')
    search_fields = ('type', 'object_id')
    date_hierarchy = ('sent')


class ReminderAdmin(admin.ModelAdmin):
    list_display = ('pk', 'journal', 'type', 'run_type',
                    'template_name', 'days', 'target_date',
                    'subject',)
    list_filter = ('journal', 'type', 'run_type', 'days', 'template_name')
    search_fields = ('journal__code', 'type', 'run_type', 'template_name')


admin_list = [
    (models.CronTask, CronTaskAdmin),
    (models.Reminder, ReminderAdmin),
    (models.SentReminder, SentReminderAdmin),
]

[admin.site.register(*t) for t in admin_list]
