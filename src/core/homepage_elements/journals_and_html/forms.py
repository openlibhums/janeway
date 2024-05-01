from django import forms
from tinymce.widgets import TinyMCE

from press import models
from journal import models as jm


class JournalsHTMLForm(forms.ModelForm):
    html_content = forms.CharField(
        widget=TinyMCE,
        label='HTML Content'
    )

    class Meta:
        model = models.Press
        fields = ('random_featured_journals', 'featured_journals')
        widgets = {
            'featured_journals': forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        self.html_setting = kwargs.pop('html_setting', None)
        super(JournalsHTMLForm, self).__init__(*args, **kwargs)

        journals = jm.Journal.objects.filter(hide_from_press=False)
        self.fields['featured_journals'].queryset = journals
        self.fields['html_content'].initial = self.html_setting.value

    def save(self, commit=True):
        press = super(JournalsHTMLForm, self).save(commit=False)

        if self.html_setting:
            self.html_setting.value = self.cleaned_data.get('html_content', '')

            if commit:
                self.html_setting.save()

        if commit:
            press.save()
