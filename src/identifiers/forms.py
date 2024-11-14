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

    def __init__(self, *args, **kwargs):
        self.article = kwargs.pop('article', None)
        self.preprint = kwargs.pop('preprint', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        super().clean()
        cleaned_data = self.cleaned_data

        id_type = cleaned_data.get('id_type')
        identifier = cleaned_data.get('identifier')

        if id_type == 'doi':
            pattern = models.DOI_RE
        else:
            pattern = models.PUB_ID_RE

        if not pattern.match(identifier):
            self.add_error(
                'identifier',
                'Invalid identifier format.',
            )

        idents = models.Identifier.objects.filter(
            id_type=id_type,
            identifier=identifier,
        )

        if self.instance:
            idents = idents.exclude(id=self.instance.id)

        if self.article:
            if id_type == 'doi' and idents.exists():
                self.add_error(
                    'identifier',
                    'This DOI already exists for another Article.',
                )
            elif idents.filter(article__journal=self.article.journal).exists():
                self.add_error(
                    'identifier',
                    'This identifier already exists on: {}.'.format(
                        " ".join([ident.article.title for ident in idents])
                    ),
                )

        elif self.preprint:
            if id_type == 'doi' and idents.exists():
                self.add_error(
                    'identifier',
                    'This DOI already exists for another Preprint.',
                )
            elif idents.filter(preprint_version__preprint__repository=self.preprint.repository).exists():
                self.add_error(
                    'identifier',
                    'This identifier already exists on: {}.'.format(
                        " ".join([ident.preprint_version.preprint.title for ident in idents])
                    ),
                )

        return cleaned_data

    def save(self, commit=True):
        identifier = super(IdentifierForm, self).save(commit=False)
        if self.article:
            identifier.article = self.article
        elif self.preprint:
            identifier.preprint_version = self.preprint.current_version

        if commit:
            identifier.save()

        return identifier
