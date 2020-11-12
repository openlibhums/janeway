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


class CombinedJournalForm(forms.ModelForm):
    journal_name = forms.CharField(label="Journal Name")
    publisher_name = forms.CharField(label="Publisher Name")
    publisher_url = forms.URLField(label="Publisher URL")
    journal_issn = forms.CharField(label="ISSN")

    field_order = [
        'journal_name',
        'code',
        'description',
        'issn',
    ]

    class Meta:
        model = journal_models.Journal
        fields = ('code', 'description')

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(CombinedJournalForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        journal = super(CombinedJournalForm, self).save(commit=True)

        keys_to_ignore = ['code', 'description']
        for setting_name, setting_value in self.cleaned_data.items():
            if setting_name not in keys_to_ignore:
                setting_handler.save_setting(
                    'general',
                    setting_name,
                    journal,
                    setting_value,
                )

        if commit:
            journal.save()
