from django import forms

from press import models
from submission import models as sub_models


class PreprintForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(PreprintForm, self).__init__(*args, **kwargs)

        self.fields['homepage_preprints'].queryset = sub_models.Article.preprints.filter(date_published__isnull=False,
                                                                                         date_declined__isnull=True)
        self.fields['homepage_preprints'].required = False

    class Meta:
        model = models.Press
        fields = ('homepage_preprints', 'random_homepage_preprints')
