__copyright__ = "Copyright 2023 Birkbeck, University of London"
__author__ = "Martin Paul Eve, Andy Byers, and Joseph Muller"
__license__ = "AGPL v3"
__maintainer__ = "Open Library of Humanities"


from django_bleach.fields import BleachField

from utils.forms import JanewayTranslationModelForm


class HTMLBlockForm(JanewayTranslationModelForm):

    content = BleachField()

    def __init__(self, *args, **kwargs):
        self.html_setting = kwargs.pop('html_setting', None)
        super().__init__(*args, **kwargs)
        self.fields['content'].initial = self.html_setting.value

    def save(self, commit=True):
        if self.html_setting:
            self.html_setting.value = self.cleaned_data.get('content', '')
            if commit:
                self.html_setting.save()
