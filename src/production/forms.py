__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django import forms

from production import models, logic
from utils.forms import HTMLDateInput
from core import models as core_models


class TypesetterNote(forms.ModelForm):
    class Meta:
        model = models.TypesetTask
        fields = ('note_from_typesetter',)


class AssignTypesetter(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.copyedit_files = kwargs.pop('files')
        self.article = kwargs.pop('article')
        self.typesetters = kwargs.pop('typesetters')
        self.assignment = kwargs.pop('assignment')

        super(AssignTypesetter, self).__init__(*args, **kwargs)

    class Meta:
        model = models.TypesetTask
        fields = (
            'typesetter',
            'files_for_typesetting',
            'due',
            'typeset_task',
        )

        widgets = {
            'due': HTMLDateInput(),
        }

    def clean(self):
        cleaned_data = super().clean()

        file_check = logic.check_posted_typesetter_files(
            self.article,
            self.copyedit_files,
            cleaned_data.get('files_for_typesetting'),
        )

        if not file_check:
            self.add_error(
                'files_for_typesetting',
                'File not found in files list.'
            )

        if not cleaned_data.get('typesetter') in logic.typesetter_users(
                self.typesetters):
            self.add_error(
                'typesetter',
                'Typesetter chosen not in list of typesetters.'
            )

    def save(self, commit=True):
        task = super(AssignTypesetter, self).save(commit=False)
        task.assignment = self.assignment

        if commit:
            task.save()

            for file in self.cleaned_data.get('files_for_typesetting'):
                task.files_for_typesetting.add(file)

        return task


class GalleyForm(forms.ModelForm):
    file = forms.FileField()

    class Meta:
        model = core_models.Galley
        fields = (
            'label',
            'public',
        )

    def __init__(self, *args, **kwargs):
        include_file = kwargs.pop('include_file', True)
        super().__init__(*args, **kwargs)
        self.fields['label'].required = False
        if not include_file:
            self.fields.pop('file')
