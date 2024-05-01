from django import forms
from tinymce.widgets import TinyMCE

from utils import setting_handler
from core.homepage_elements.about import plugin_settings


class AboutForm(forms.Form):
    title = forms.CharField(
        help_text='The title of the about block eg. "About this Journal"',
    )
    description = forms.CharField(
        widget=TinyMCE,
        help_text='A general description of the journal.',
    )

    def save(self, journal, commit=True):
        title = self.cleaned_data.get('title')
        description = self.cleaned_data.get('description')

        if commit:
            setting_handler.save_plugin_setting(
                plugin_settings.get_self(),
                'about_title',
                title,
                journal,
            )

            setting_handler.save_setting(
                'general',
                'journal_description',
                journal,
                description,
            )
