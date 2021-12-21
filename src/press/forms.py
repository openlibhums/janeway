__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django import forms

from press import models
from core.widgets import JanewayFileInput
from core import files, logic
from core.middleware import GlobalRequestMiddleware


class PressForm(forms.ModelForm):

    press_logo = forms.FileField(
        required=False,
        widget=JanewayFileInput,
    )

    class Meta:
        model = models.Press
        fields = (
            'name', 'main_contact', 'theme', 'footer_description',
            'default_carousel_image', 'favicon', 'enable_preprints',
            'is_secure', 'password_number', 'password_upper',
            'password_length', 'password_reset_text', 'registration_text',
            'tracking_code', 'disable_journals', 'privacy_policy_url',
        )
        widgets = {
            'theme': forms.Select(
                choices=logic.get_theme_list()
            )
        }

    def save(self, commit=True):
        press = super(PressForm, self).save(commit=False)
        request = GlobalRequestMiddleware.get_current_request()

        file = self.cleaned_data.get('press_logo', None)

        if file:
            file = files.save_file_to_press(request, file, 'Press Logo', '')

            # Delete the old file from the disk
            if press.thumbnail_image:
                press.thumbnail_image.delete()

            press.thumbnail_image = file

        if commit:
            press.save()

        return press

