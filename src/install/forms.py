__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
from django import forms

from journal import models as journal_models
from utils import setting_handler


class JournalForm(forms.ModelForm):

    class Meta:
        model = journal_models.Journal
        fields = ('code', 'description')


class JournalSettingsForm(forms.Form):

    journal_name = forms.CharField(label="Journal Name")
    publisher_name = forms.CharField(label="Publisher Name")
    publisher_url = forms.URLField(label="Publisher URL")
    journal_issn = forms.CharField(label="ISSN")

    def save(self, request, commit=True):
        for setting_name, setting_value in self.cleaned_data.items():
            test = setting_handler.save_setting('general', setting_name, request.journal, setting_value)
