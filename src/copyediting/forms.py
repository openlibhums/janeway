__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django import forms

from copyediting import models


class CopyeditAssignmentForm(forms.ModelForm):
    class Meta:
        model = models.CopyeditAssignment
        fields = ('editor_note', 'due')


class CopyEditForm(forms.ModelForm):
    class Meta:
        model = models.CopyeditAssignment
        fields = ('copyeditor_note',)


class AuthorCopyeditForm(forms.ModelForm):
    class Meta:
        model = models.AuthorReview
        fields = ('decision', 'author_note')
