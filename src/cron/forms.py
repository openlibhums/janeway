__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django import forms

from cron import models


class ReminderForm(forms.ModelForm):

    class Meta:
        model = models.Reminder
        exclude = ('journal',)
