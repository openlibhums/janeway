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
    class Meta:
        model = models.TypesetterProofingTask
        fields = ('due', 'task')

    def __init__(self, *args, **kwargs):
        comments = kwargs.pop('comments', None)
        super(AssignTypesetter, self).__init__(*args, **kwargs)

        self.fields['due'].required = True
        if comments:
            self.fields['task'].initial = comments


class CompleteCorrections(forms.ModelForm):
    class Meta:
        model = models.TypesetterProofingTask
        fields = ('notes',)

    def __init__(self, *args, **kwargs):
        super(CompleteCorrections, self).__init__(*args, **kwargs)

        self.fields['notes'].required = True
