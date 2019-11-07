from django import forms

from utils import setting_handler
from core.homepage_elements.about import plugin_settings


class FeaturedForm(forms.Form):
    most_downloaded = forms.BooleanField(
        label='Display Most Downloaded Articles',
        help_text='Displays the most downloaded articles.',
    )
    num_most_downloaded = forms.IntegerField(
        label='Number of Most Downloaded Articles to Display',
        help_text='Determines how many popular articles we should display.',
    )
    most_downloaded_time = forms.ChoiceField(
        choices=(
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('yearly', 'Yearly'),
        ),
        label='Number of Most Downloaded Articles to Display',
        help_text='Determines how many popular articles we should display.',
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
