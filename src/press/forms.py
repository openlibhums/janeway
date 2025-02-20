__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django import forms
from tinymce.widgets import TinyMCE

from press import models
from core.widgets import JanewayFileInput
from core import files, logic
from core.middleware import GlobalRequestMiddleware
from utils import setting_handler


class PressForm(forms.ModelForm):

    press_logo = forms.FileField(
        required=False,
        widget=JanewayFileInput,
    )

    class Meta:
        model = models.Press
        fields = (
            'name',
            'main_contact',
            'theme',
            'description',
            'footer_description',
            'journal_footer_text',
            'secondary_image',
            'secondary_image_url',
            'default_carousel_image',
            'favicon',
            'enable_preprints',
            'is_secure',
            'password_number',
            'password_upper',
            'password_length',
            'tracking_code',
            'disable_journals',
            'privacy_policy_url',
        )
        widgets = {
            'theme': forms.Select(
                choices=logic.get_theme_list()
            ),
            'footer_description': TinyMCE(),
            'journal_footer_text': TinyMCE(),
            'description': TinyMCE(),
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


class PressJournalDescription(forms.Form):

    description = forms.CharField(widget=TinyMCE)

    def __init__(self, *args, **kwargs):
        self.journal = kwargs.pop('journal')
        super(PressJournalDescription, self).__init__(*args, **kwargs)
        self.fields['description'].initial = self.journal.get_setting(
            group_name='general',
            setting_name='press_journal_description',
        )

    def save(self, commit=True):
        description = self.cleaned_data.get('description')

        if commit:
            setting_handler.save_setting(
                'general',
                'press_journal_description',
                self.journal,
                description,
            )

class StaffGroupMemberForm(forms.ModelForm):
    """Lets a staff member edit a few fields related to their
    press staff profile
    """
    class Meta:
        model = models.StaffGroupMember
        exclude = ('group', 'user', 'sequence')
        widgets = {
            'publications': TinyMCE(),
        }
