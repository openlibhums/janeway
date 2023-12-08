from django import forms

from utils import setting_handler
from core.homepage_elements.popular import plugin_settings, logic


class NewsForm(forms.Form):
    number_of_articles = forms.IntegerField(
        help_text='Number of news articles to display on the homepage.'
    )
    display_images = forms.BooleanField(
        help_text='When enabled the News Plugin will display news images. '
                  'Note: this setting has no effect on the clean theme '
                  'which does not display images for news.',
        required=False
    )

    def __init__(self, *args, **kwargs):
        self.journal = kwargs.pop('journal', None)
        super(NewsForm, self).__init__(*args, **kwargs)
        number_of_articles = setting_handler.get_setting(
            'plugin:News',
            'number_of_articles',
            self.journal,
        )
        display_images = setting_handler.get_setting(
            'plugin:News',
            'display_images',
            self.journal,
        )
        self.fields['number_of_articles'].initial = number_of_articles.value
        self.fields['display_images'].initial = True if display_images.value else False

    def save(self, commit=True):
        number_of_articles = self.cleaned_data.get('number_of_articles')
        display_images = self.cleaned_data.get('display_images')

        if commit:
            setting_handler.save_setting(
                'plugin:News',
                'number_of_articles',
                self.journal,
                number_of_articles,
            )
            setting_handler.save_setting(
                'plugin:News',
                'display_images',
                self.journal,
                'On' if display_images else '',
            )

