from django import forms
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from core import models as core_models, forms as core_forms
from core.model_utils import JanewayBleachFormField
from typesetting import models
from utils.forms import HTMLDateInput


class TypesettingAssignmentForm(
    forms.ModelForm,
    core_forms.ConfirmableIfErrorsForm
):

    # Confirmable form modification
    QUESTION = _('Are you sure you want to create a typesetting assignment?')

    def __init__(self, *args, **kwargs):
        typesetters = kwargs.pop('typesetters')
        files = kwargs.pop('files')
        galleys = kwargs.pop('galleys', ())
        initial_galleys_to_correct = kwargs.pop('initial_galleys_to_correct', ())
        self.rounds = kwargs.pop('rounds')
        super().__init__(*args, **kwargs)

        self.fields['typesetter'].queryset = typesetters
        self.fields['files_to_typeset'].queryset = files
        self.fields['galleys_to_correct'] = forms.MultipleChoiceField(
            widget=forms.CheckboxSelectMultiple(),
            required=False,
            choices=[(g.pk, g.detail()) for g in galleys],
            initial=initial_galleys_to_correct,
        )

    class Meta:
        model = models.TypesettingAssignment
        fields = (
            'typesetter',
            'due',
            'task',
            'files_to_typeset',
            'display_proof_comments',
        )

        widgets = {
            'due': HTMLDateInput(),
        }

    def save(self, commit=True):
        assignment = super().save(commit=False)
        assignment.round = self.rounds[0]

        if commit:
            with transaction.atomic():
                assignment.save()

                for file in assignment.files_to_typeset.all():
                    assignment.files_to_typeset.remove(file)
                for file in self.cleaned_data.get('files_to_typeset', ()):
                    assignment.files_to_typeset.add(file)

                galleys_to_correct = self.cleaned_data.get('galleys_to_correct', ())
                for correction in assignment.corrections.all():
                    if correction.galley.pk not in galleys_to_correct:
                        correction.delete()
                for galley_id in galleys_to_correct:
                    galley = core_models.Galley.objects.get(pk=galley_id)
                    assignment.corrections.get_or_create(
                        task=assignment,
                        galley=galley,
                        label=galley.label,
                    )

        return assignment

    def check_for_potential_errors(self):
        # Confirmable form modification
        potential_errors = []

        typesetter = self.cleaned_data.get('typesetter', None)
        message = self.check_for_inactive_account(typesetter)
        if message:
            potential_errors.append(message)

        files_to_typeset = self.cleaned_data.get('files_to_typeset', ())
        if not files_to_typeset:
            message = "No files were selected for typesetting. The typesetter " \
                      "may not have access to the right files."
            potential_errors.append(message)

        galleys_to_correct = self.cleaned_data.get('galleys_to_correct', ())
        if not galleys_to_correct and self.rounds.first().article.galley_set.exists():
            message = "No galleys were marked for correction."
            potential_errors.append(message)

        for galley_id in galleys_to_correct:
            try:
                galley = core_models.Galley.objects.get(pk=galley_id)
                if galley.file not in files_to_typeset:
                    message = f"The galley with a label of {galley.label} " \
                              f"was selected for correction, but the typesetter " \
                              f"was not given access to the linked " \
                              f"file: {galley.file.pk} - {galley.file.original_filename}."
                    potential_errors.append(message)
            except core_models.Galley.DoesNotExist:
                pass

        return potential_errors

    def last_typesetter(self):
        if len(self.rounds) > 1:
            return self.rounds[1].typesettingassignment.typesetter
        else:
            return None


class EditTypesettingAssignmentForm(TypesettingAssignmentForm):
    QUESTION = _('Are you sure you want to save the typesetting assignment?')
    CONFIRMABLE_BUTTON_NAME = 'edit_confirmable'
    CONFIRMED_BUTTON_NAME = 'edit_confirmed'


class AssignProofreader(forms.ModelForm, core_forms.ConfirmableIfErrorsForm):

    # Confirmable form modification
    QUESTION = _('Are you sure you want to create a proofreading assignment?')

    def __init__(self, *args, **kwargs):
        self.proofreaders = kwargs.pop('proofreaders')
        self.round = kwargs.pop('round')
        self.manager = kwargs.pop('user')
        super(AssignProofreader, self).__init__(*args, **kwargs)

        self.fields['proofreader'].queryset = self.proofreaders

    class Meta:
        model = models.GalleyProofing
        fields = ('proofreader', 'task', 'due',)

        widgets = {
            'due': HTMLDateInput(),
        }

    def save(self, commit=True):
        assignment = super(AssignProofreader, self).save(commit=False)
        assignment.round = self.round
        assignment.manager = self.manager

        if commit:
            assignment.save()

        return assignment

    def check_for_potential_errors(self):
        # Confirmable form modification
        potential_errors = []

        proofreader = self.cleaned_data.get('proofreader', None)
        message = self.check_for_inactive_account(proofreader)
        if message:
            potential_errors.append(message)

        return potential_errors


def decision_choices():
    return (
        ('accept', 'Accept'),
        ('decline', 'Decline'),
    )


class TypesetterDecision(forms.Form):
    decision = forms.ChoiceField(choices=decision_choices(), required=True)
    note = JanewayBleachFormField(required=False)


class ManagerDecision(forms.ModelForm):

    class Meta:
        model = models.TypesettingAssignment
        fields = ('review_decision',)

    def save(self, commit=True):
        decision = super(ManagerDecision, self).save(commit=False)
        decision.reviewed = True
        if commit:
            decision.save()

        return decision


class SupplementaryFileChoiceForm(forms.ModelForm):
    label = forms.CharField(
        required=False,
        help_text=_("Text to show as the download link on the article page")
    )

    def __init__(self, *args, **kwargs):
        self.article = kwargs.pop('article')
        super().__init__(*args, **kwargs)
        files = core_models.File.objects.filter(
            article_id=self.article.pk,
        ).exclude(
            supplementaryfile__file__article_id = self.article.pk,
        )
        self.fields['file'].queryset = files

    class Meta:
        model = core_models.SupplementaryFile
        fields = ('file',)

    def save(self, commit=True):
        instance = super().save(commit=commit)
        if commit:
            if self.cleaned_data.get("label"):
                instance.file.label = self.cleaned_data["label"]
                instance.file.save()
            self.article.supplementary_files.add(instance)
        return instance


class EditProofingAssignment(forms.ModelForm):
    class Meta:
        model = models.GalleyProofing
        fields = ('task', 'due',)
        widgets = {
            'due': HTMLDateInput(),
        }


class ProofingForm(forms.ModelForm, core_forms.ConfirmableForm):

    # Confirmable form constants
    QUESTION = _('Are you sure you want to complete the proofreading task?')

    class Meta:
        model = models.GalleyProofing
        fields = ('notes',)
        summernote_attrs = {
            'disable_attachment': True,
            'height': '500px',
        }

    def check_for_potential_errors(self):
        # This customizes the confirmable form method
        potential_errors = []

        # Check for unproofed galleys
        galleys = core_models.Galley.objects.filter(
            article=self.instance.round.article,
        )
        unproofed_galleys = self.instance.unproofed_galleys(galleys)
        if unproofed_galleys:
            message = _('You have not proofed some galleys:')+' {}.'.format(
                        ", ".join([g.label for g in unproofed_galleys])
                    )
            potential_errors.append(message)

        # Check if a note was added
        if not self.cleaned_data.get('notes', None):
            message = 'The Notes field is empty.'
            potential_errors.append(_(message))

        # Check if new files were added
        annotated_files = self.instance.annotated_files.all()
        if annotated_files:
            last_upload = max(set(an_file.date_uploaded for an_file in annotated_files))
            last_editor_or_typesetter_action = max(filter(bool, [
                self.instance.completed,
                self.instance.assigned,
            ]))
            if last_editor_or_typesetter_action > last_upload:
                message = 'The annotated files have not been changed.'
                potential_errors.append(_(message))
        else:
            message = 'No annotated files have been uploaded.'
            potential_errors.append(_(message))

        return potential_errors


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
