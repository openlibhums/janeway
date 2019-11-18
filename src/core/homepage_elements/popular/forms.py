from django import forms

from utils import setting_handler
from core.homepage_elements.popular import plugin_settings, logic


class FeaturedForm(forms.Form):

    def __init__(self, *args, **kwargs):
        self.journal = kwargs.pop('journal', None)
        super(FeaturedForm, self).__init__(*args, **kwargs)

        most_popular, num_most_popular, most_popular_time = logic.get_popular_article_settings(
            self.journal
        )

        self.fields['num_most_popular'].initial = num_most_popular
        self.fields['most_popular'].initial = most_popular
        self.fields['most_popular_time'].initial = most_popular_time

    most_popular = forms.BooleanField(
        label='Display Most Popular Articles',
        help_text='Displays the most popular articles.',
        required=False,
    )
    num_most_popular = forms.IntegerField(
        label='Number of Most Popular Articles to Display',
        help_text='Determines how many popular articles we should display.',
    )
    most_popular_time = forms.ChoiceField(
        choices=(
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('yearly', 'Yearly'),
        ),
        label='Number of Most Popular Articles to Display',
        help_text='Determines how many popular articles we should display.',
    )

    def save(self, commit=True):
        most_popular = self.cleaned_data.get('most_popular')
        num_most_popular = self.cleaned_data.get('num_most_popular', 0)
        most_popular_time = self.cleaned_data.get('most_popular_time')

        if commit:
            setting_handler.save_plugin_setting(
                plugin_settings.get_self(),
                'most_popular',
                most_popular,
                self.journal,
            )

            setting_handler.save_plugin_setting(
                plugin_settings.get_self(),
                'num_most_popular',
                num_most_popular,
                self.journal,
            )

            setting_handler.save_plugin_setting(
                plugin_settings.get_self(),
                'most_popular_time',
                most_popular_time,
                self.journal,
            )

