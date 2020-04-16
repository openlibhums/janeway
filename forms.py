from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction

from django_summernote.widgets import SummernoteWidget

from core import models as core_models
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
            choices=[(g.pk, g.label) for g in galleys],
            help_text='Select which galleys require corrections '
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

                for galley_id in self.cleaned_data.get("corrections"):
                    correction, _ = assignment.corrections.get_or_create(
                        task=assignment,
                        galley=core_models.Galley.objects.get(pk=galley_id),
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


class EditProofingAssignment(forms.ModelForm):
    class Meta:
        model = models.GalleyProofing
        fields = ('task', 'due',)
        widgets = {
            'due': HTMLDateInput(),
        }


class ProofingForm(forms.ModelForm):
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
