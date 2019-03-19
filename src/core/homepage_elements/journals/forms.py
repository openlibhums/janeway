from django import forms

from press import models
from journal import models as jm


class FeaturedJournalsForm(forms.ModelForm):
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
