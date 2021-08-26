__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django import forms
from django.utils.text import slugify

from cron import models


class ReminderForm(forms.ModelForm):

    class Meta:
        model = models.Reminder
        exclude = ('journal',)

    def __init__(self, *args, **kwargs):
        self.journal = kwargs.pop('journal')
        super(ReminderForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        reminder = super(ReminderForm, self).save(commit=False)
        reminder.journal = self.journal
        reminder.template_name = slugify(reminder.template_name)

        if commit:
            reminder.save()

        return reminder
