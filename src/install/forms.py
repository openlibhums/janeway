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


class BaseJournalForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.setting_group = kwargs.pop('setting_group')
        self.model_keys = kwargs.pop('model_keys')
        super(BaseJournalForm, self).__init__(*args, **kwargs)

        # If we have a journal we want to set initial values
        if self.instance:
            for field_name, field in self.fields.items():
                if field_name not in self.model_keys:
                    field.initial = self.instance.get_setting(
                        self.setting_group,
                        field_name,
                    )

    def save(self, commit=True):
        journal = super(BaseJournalForm, self).save(commit=True)
        for setting_name, setting_value in self.cleaned_data.items():
            if setting_name not in self.model_keys:
                setting_handler.save_setting(
                    'general',
                    setting_name,
                    journal,
                    setting_value,
                )

        if commit:
            journal.save()


class CombinedJournalForm(BaseJournalForm):
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
