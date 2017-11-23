__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django.contrib import admin
from cron import models

admin_list = [
    (models.CronTask,),
    (models.Reminder,),
    (models.SentReminder,),
]

[admin.site.register(*t) for t in admin_list]
