__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django.contrib import admin
from cron import models
from utils import admin_utils
from review import models as review_models


class CronTaskAdmin(admin.ModelAdmin):
    list_display = ('task_type', 'run_at', 'article')
    list_filter = ('article__journal__code', 'email_journal',
                   'task_type', 'added', 'run_at')
    search_fields = ('article__title', 'email_to', 'email_cc',
                     'email_html', 'email_bcc', 'task_data')
    raw_id_fields = ('article',)


class SentReminderAdmin(admin.ModelAdmin):
    list_display = ('type', '_object', 'sent')
    list_filter = (admin_utils.SentReminderJournalFilter,
                   'type', 'sent')
    search_fields = ('type', 'object_id')
    date_hierarchy = ('sent')
    readonly_fields = ('_object',)

    def _object(self, obj):
        if not obj:
            return ''

        if obj.type == 'review':
            model = review_models.ReviewAssignment
        elif obj.type == 'accepted-review':
            model = review_models.ReviewAssignment
        elif obj.type == 'revisions':
            model = review_models.RevisionRequest
        return model.objects.get(id=obj.object_id)


class ReminderAdmin(admin.ModelAdmin):
    list_display = ('type', 'run_type',
                    'template_name', 'days', 'target_date',
                    'subject', 'journal')
    list_filter = ('journal__code', 'type', 'run_type', 'days',
                   'template_name')
    search_fields = ('journal__code', 'type', 'run_type', 'template_name')


admin_list = [
    (models.CronTask, CronTaskAdmin),
    (models.Reminder, ReminderAdmin),
    (models.SentReminder, SentReminderAdmin),
]

[admin.site.register(*t) for t in admin_list]
