from django import forms
from django.core.exceptions import ValidationError
from submission.models import FieldChoice


class FieldChoiceForm(forms.ModelForm):
    class Meta:
        model = FieldChoice
        fields = ['real_value', 'display_value']
        widgets = {
            'real_value': forms.TextInput(attrs={'class': 'form-control'}),
            'display_value': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['real_value'].widget.attrs.update({'class': 'form-control'})
        self.fields['display_value'].widget.attrs.update({'class': 'form-control'})
    
    def clean_real_value(self):
        real_value = self.cleaned_data.get('real_value')
        if not real_value:
            raise ValidationError("Real value is required.")
        return real_value
    
    def clean_display_value(self):
        display_value = self.cleaned_data.get('display_value')
        if not display_value:
            raise ValidationError("Display value is required.")
        return display_value


class FieldChoicesManagementForm(forms.Form):
    """
    Form for managing multiple field choices at once.
    """
    def __init__(self, field, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.field = field
        self.choices = field.field_choices.all().order_by('order')
        
        # Add fields for each existing choice
        for choice in self.choices:
            self.fields[f'real_value_{choice.id}'] = forms.CharField(
                initial=choice.real_value,
                required=True,
                widget=forms.TextInput(attrs={'class': 'form-control'})
            )
            self.fields[f'display_value_{choice.id}'] = forms.CharField(
                initial=choice.display_value,
                required=True,
                widget=forms.TextInput(attrs={'class': 'form-control'})
            )
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validate that real values are unique within the field
        real_values = []
        for choice in self.choices:
            real_value_key = f'real_value_{choice.id}'
            if real_value_key in cleaned_data:
                real_value = cleaned_data[real_value_key]
                if real_value in real_values:
                    raise ValidationError(f"Duplicate real value found: {real_value}")
                real_values.append(real_value)
        
        return cleaned_data