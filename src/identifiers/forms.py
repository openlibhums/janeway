import re

from django import forms

from identifiers import models


class IdentifierForm(forms.ModelForm):

    class Meta:
        model = models.Identifier
        fields = (
            'id_type',
            'identifier',
            'enabled',
        )

    def clean(self):
        cleaned_data = self.cleaned_data
        id_type = self.cleaned_data.get('id_type')
        identifier = self.cleaned_data.get('identifier')

        if id_type == 'doi':
            pattern = models.DOI_RE
        else:
            pattern = models.PUB_ID_RE

        if not pattern.match(identifier):
            self.add_error(
                'identifier',
                'Invalid identifier format.',
            )

        return cleaned_data

    def save(self, article=None, commit=True):
        identifier = super(IdentifierForm, self).save(commit=False)

        if article:
            identifier.article = article

        if commit:
            pass
            identifier.save()

        return identifier
