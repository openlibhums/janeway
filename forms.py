from django import forms

from plugins.typesetting import models
from utils.forms import HTMLDateInput


class AssignTypesetter(forms.ModelForm):
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

