__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django import forms
from django.utils.translation import gettext as _

from core.models import Account
from core import forms as core_forms
from copyediting import models
from utils.forms import HTMLDateInput


class CopyeditAssignmentForm(forms.ModelForm, core_forms.ConfirmableIfErrorsForm):
    QUESTION = _('Are you sure you want to create a copyediting assignment?')

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
            'due': HTMLDateInput,
        }

    def __init__(self, *args, **kwargs):
        copyeditor_pks = kwargs.pop('copyeditor_pks', None)
        files = kwargs.pop('files', None)
        self.editor = kwargs.pop('editor', None)
        self.article = kwargs.pop('article', None)
        super(CopyeditAssignmentForm, self).__init__(*args, **kwargs)

        if copyeditor_pks:
            self.fields['copyeditor'].queryset = Account.objects.filter(
                pk__in=copyeditor_pks,
            )

        if files:
            self.fields['files_for_copyediting'].queryset = files

    def save(self, commit=True):
        copyedit = super(CopyeditAssignmentForm, self).save(commit=False)
        copyedit.copyeditor = self.cleaned_data.get('copyeditor')
        copyedit.editor = self.editor
        copyedit.article = self.article

        if commit:
            copyedit.save()

            # If saving, an instance exists so we can now add the files.
            copyedit.files_for_copyediting.add(
                *self.cleaned_data.get('files_for_copyediting'),
            )

        return copyedit

    def check_for_potential_errors(self):
        # This customizes the confirmable form method
        potential_errors = []

        copyeditor = self.cleaned_data.get('copyeditor', None)
        message = self.check_for_inactive_account(copyeditor)
        if message:
            potential_errors.append(message)

        return potential_errors


class EditCopyeditAssignment(forms.ModelForm):
    class Meta:
        model = models.CopyeditAssignment
        fields = (
            'editor_note',
            'due',
        )
        widgets = {
            'due': HTMLDateInput,
        }


class CopyEditForm(forms.ModelForm):
    class Meta:
        model = models.CopyeditAssignment
        fields = ('copyeditor_note',)


class AuthorReviewAssignmentForm(forms.ModelForm, core_forms.ConfirmableForm):

    # Note: This form uses ConfirmableForm rather than ConfirmableIfErrorsForm
    # because there is no first step to the task creation, as with other stages,
    # so the modal provides a way back if the button is accidentally clicked.

    # Confirmable form constants
    QUESTION = _('Are you sure you want to ask the author to review copyedits?')
    CONFIRMABLE_BUTTON_NAME = 'author_review'

    class Meta:
        model = models.AuthorReview

        # This field is not for user input,
        # just to make form validation operable
        fields = ('author',)

    def __init__(self, *args, **kwargs):
        self.author = kwargs.pop('author', None)
        self.assignment = kwargs.pop('assignment', None)
        self.notified = kwargs.pop('notified', False)
        super().__init__(*args, **kwargs)

        # The way the author field works is a
        # a temporary workaround arising
        # from the desire to use core_models.ConfirmableForm
        # for consistency with other assignments.
        self.fields['author'].required = False


    def save(self, commit=True):
        review_assignment = super().save(commit=False)
        review_assignment.author = self.author
        review_assignment.assignment = self.assignment

        if commit:
            review_assignment.save()

        return review_assignment

    def check_for_potential_errors(self):
        # This customizes the confirmable form method
        potential_errors = []

        message = self.check_for_inactive_account(self.author)
        if message:
            potential_errors.append(message)

        return potential_errors


class AuthorCopyeditForm(forms.ModelForm, core_forms.ConfirmableForm):

    # Confirmable form constants
    QUESTION = _('Are you sure you want to complete the copyedit task?')

    class Meta:
        model = models.AuthorReview
        fields = ('decision', 'author_note')

    def __init__(self, *args, **kwargs):
        super(AuthorCopyeditForm, self).__init__(*args, **kwargs)
        self.fields['decision'].required = True

    def check_for_potential_errors(self):
        # This customizes the confirmable form method
        potential_errors = []

        if not self.cleaned_data.get('author_note', None):
            message = 'The Note to the Editor field is empty.'
            potential_errors.append(_(message))

        copyedit = self.instance.assignment
        ce_files = copyedit.copyeditor_files.all()
        if ce_files:
            last_upload = max(set(ce_file.date_uploaded for ce_file in ce_files))
            last_editor_action = max(filter(bool, [
                copyedit.copyeditor_completed,
                copyedit.copyedit_reopened_complete,
                copyedit.assigned
            ]))
            if last_editor_action > last_upload:
                message = 'The copyedited files have not been changed.'
                potential_errors.append(_(message))

        return potential_errors

