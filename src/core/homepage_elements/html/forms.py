from django import forms
from tinymce.widgets import TinyMCE

from utils import setting_handler
from core.homepage_elements.html import plugin_settings


class HTMLForm(forms.Form):
    html_content = forms.CharField(
        widget=TinyMCE,
        label='HTML Content',
    )

    def save(self, journal, commit=True):
        html_content = self.cleaned_data.get('html_content')

        if commit:
            setting_handler.save_plugin_setting(
                plugin_settings.get_self(),
                'html_block_content',
                html_content,
                journal,
            )
