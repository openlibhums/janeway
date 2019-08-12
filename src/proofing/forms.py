__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
from django import forms

from proofing import models


class AssignProofreader(forms.ModelForm):
    class Meta:
        model = models.ProofingTask
        fields = ('due', 'task')
        widgets = {'galleys_for_proofing': forms.CheckboxSelectMultiple}


class AssignTypesetter(forms.ModelForm):
    include_comments = forms.BooleanField()

    class Meta:
        model = models.TypesetterProofingTask
        fields = ('due', 'task')

    def __init__(self, *args, **kwargs):
        comments = kwargs.pop('comments', None)
        super(AssignTypesetter, self).__init__(*args, **kwargs)

        self.fields['due'].required = True
        if comments:
            self.fields['task'].initial = comments

    def save(self, proofing_task, user, comments, commit=True):
        typeset_task = super(AssignTypesetter, self).save(commit=False)
        typeset_task.typesetter = user
        typeset_task.proofing_task = proofing_task

        if self.cleaned_data['include_comments']:
            typeset_task.task = '{0}<br />{1}'.format(
                typeset_task.task,
                comments,
            )

        if commit:
            typeset_task.save()

        return typeset_task


class CompleteCorrections(forms.ModelForm):
    class Meta:
        model = models.TypesetterProofingTask
        fields = ('notes',)

    def __init__(self, *args, **kwargs):
        super(CompleteCorrections, self).__init__(*args, **kwargs)

        self.fields['notes'].required = True
