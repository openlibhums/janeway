__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django import forms

from core.models import Account
from copyediting import models


class CopyeditAssignmentForm(forms.ModelForm):
    class Meta:
        model = models.CopyeditAssignment
        fields = (
            'editor_note',
            'due',
            'files_for_copyediting',
            'copyeditor',
        )

        attrs = {'required': True}

        widgets = {
            'files_for_copyediting': forms.CheckboxSelectMultiple(attrs=attrs),
            'copyeditor': forms.RadioSelect(attrs=attrs),
        }

    def __init__(self, *args, **kwargs):
        copyeditor_pks = kwargs.pop('copyeditor_pks', None)
        files = kwargs.pop('files', None)
        super(CopyeditAssignmentForm, self).__init__(*args, **kwargs)

        if copyeditor_pks:
            self.fields['copyeditor'].queryset = Account.objects.filter(
                pk__in=copyeditor_pks,
            )

        if files:
            self.fields['files_for_copyediting'].queryset = files

    def save(self, editor=None, article=None, commit=True):
        copyedit = super(CopyeditAssignmentForm, self).save(commit=False)
        copyedit.copyeditor = self.cleaned_data.get('copyeditor')

        if editor:
            copyedit.editor = editor

        if article:
            copyedit.article = article

        if commit:
            copyedit.save()

            # If saving, an instance exists so we can now add the files.
            copyedit.files_for_copyediting.add(
                *self.cleaned_data.get('files_for_copyediting'),
            )

        return copyedit


class CopyEditForm(forms.ModelForm):
    class Meta:
        model = models.CopyeditAssignment
        fields = ('copyeditor_note',)


class AuthorCopyeditForm(forms.ModelForm):
    class Meta:
        model = models.AuthorReview
        fields = ('decision', 'author_note')

    def __init__(self, *args, **kwargs):
        super(AuthorCopyeditForm, self).__init__(*args, **kwargs)
        self.fields['decision'].required = True
