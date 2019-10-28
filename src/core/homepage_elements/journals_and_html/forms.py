from django import forms

from press import models
from journal import models as jm
from django_summernote.widgets import SummernoteWidget


class FeaturedJournalsForm(forms.ModelForm):
    html_content = forms.CharField(
        widget=SummernoteWidget,
        label='HTML Content'
    )

    class Meta:
        model = models.Press
        fields = ('random_featured_journals', 'featured_journals')
        widgets = {
            'featured_journals': forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        super(FeaturedJournalsForm, self).__init__(*args, **kwargs)

        journals = jm.Journal.objects.filter(hide_from_press=False)
        self.fields['featured_journals'].queryset = journals

    def save(self, commit=True, html_setting=None):
        press = super(FeaturedJournalsForm, self).save(commit=False)

        if html_setting:
            html_setting.value = self.cleaned_data.get('html_content', '')

            if commit:
                html_setting.save()

        if commit:
            press.save()
