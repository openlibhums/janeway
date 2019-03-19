__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django import forms

from press import models
from core.widgets import JanewayFileInput
from core import files
from core.middleware import GlobalRequestMiddleware


class PressForm(forms.ModelForm):

    press_logo = forms.FileField(
        required=False,
        widget=JanewayFileInput,
    )

    class Meta:
        model = models.Press
        exclude = (
            'domain', 'preprints_about', 'preprint_start', 'preprint_pdf_only',
            'preprint_submission', 'preprint_publication', 'preprint_editors',
            'random_homepage_preprints', 'homepage_preprints', 'carousel_type',
            'carousel_items', 'homepage_news_items', 'carousel',
            'carousel_news_items', 'thumbnail_image',
        )
        widgets = {
            'featured_journals': forms.CheckboxSelectMultiple,
        }

    def save(self, commit=True):
        press = super(PressForm, self).save(commit=False)
        request = GlobalRequestMiddleware.get_current_request()

        if press.thumbnail_image:
            press.thumbnail_image.delete()

        file = self.cleaned_data['press_logo']
        file = files.save_file_to_press(request, file, 'Press Logo', '')
        press.thumbnail_image = file

        if commit:
            press.save()

        return press

