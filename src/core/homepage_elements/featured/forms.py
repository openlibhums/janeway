from django import forms

from utils import setting_handler
from core.homepage_elements.featured import plugin_settings, logic


class FeaturedForm(forms.Form):

    def __init__(self, *args, **kwargs):
        journal = kwargs.pop('journal', None)
        super(FeaturedForm, self).__init__(*args, **kwargs)

        most_downloaded, num_most_downloaded, most_downloaded_time = logic.get_popular_article_settings(
            journal
        )

        self.fields['num_most_downloaded'].initial = num_most_downloaded
        self.fields['most_downloaded'].initial = most_downloaded
        self.fields['most_downloaded_time'].initial = most_downloaded_time

    most_downloaded = forms.BooleanField(
        label='Display Most Downloaded Articles',
        help_text='Displays the most downloaded articles.',
        required=False,
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
        most_downloaded = self.cleaned_data.get('most_downloaded')
        num_most_downloaded = self.cleaned_data.get('num_most_downloaded', 0)
        most_downloaded_time = self.cleaned_data.get('most_downloaded_time')

        if commit:
            setting_handler.save_plugin_setting(
                plugin_settings.get_self(),
                'most_downloaded',
                most_downloaded,
                journal,
            )

            setting_handler.save_plugin_setting(
                plugin_settings.get_self(),
                'num_most_downloaded',
                num_most_downloaded,
                journal,
            )

            setting_handler.save_plugin_setting(
                plugin_settings.get_self(),
                'most_downloaded_time',
                most_downloaded_time,
                journal,
            )

