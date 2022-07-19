from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import ugettext_lazy as _

from django_summernote.widgets import SummernoteWidget

from core import models as core_models, forms as core_forms
from plugins.typesetting import models
from utils.forms import HTMLDateInput


class AssignTypesetter(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        typesetters = kwargs.pop('typesetters')
        files = kwargs.pop('files')
        galleys = kwargs.pop('galleys', ())
        self.rounds = kwargs.pop('rounds')
        super(AssignTypesetter, self).__init__(*args, **kwargs)

        self.fields['typesetter'].queryset = typesetters
        self.fields['files_to_typeset'].queryset = files
        self.fields['corrections'] = forms.MultipleChoiceField(
            required=False,
            choices=[(g.pk, g.label) for g in galleys],
            help_text='Select which files require corrections '
                      '(Click and drag to select multiple)',
            initial=[galley.pk for galley in galleys],
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
        assignment = super(AssignTypesetter, self).save(commit=False)
        assignment.round = self.rounds[0]

        if commit:
            with transaction.atomic():
                assignment.save()

                for file in self.cleaned_data.get('files_to_typeset'):
                    assignment.files_to_typeset.add(file)

                for galley_id in self.cleaned_data.get("corrections", []):
                    galley = core_models.Galley.objects.get(pk=galley_id)
                    correction, _ = assignment.corrections.get_or_create(
                        task=assignment,
                        galley=galley,
                        label=galley.label,
                    )

        return assignment

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('files_to_typeset'):
            raise ValidationError("At least one file must be made picked")


class AssignProofreader(forms.ModelForm):

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


def decision_choices():
    return (
        ('accept', 'Accept'),
        ('decline', 'Decline'),
    )


class TypesetterDecision(forms.Form):
    decision = forms.ChoiceField(choices=decision_choices(), required=True)
    note = forms.CharField(widget=forms.Textarea, required=False)


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
        widgets = {
            'notes': SummernoteWidget(
                attrs={'summernote': summernote_attrs},
            ),
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
