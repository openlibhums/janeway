__copyright__ = "Copyright 2022 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
from django import forms
from django.urls import reverse

from core import files, forms as core_forms
from journal import models


class NewIssue(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        journal = kwargs.pop("journal")
        super().__init__(*args, **kwargs)
        self.fields["issue_type"].queryset = models.IssueType.objects.filter(
            journal=journal)
        if self.instance and self.instance.code:
            path = reverse(
                "journal_collection_by_code",
                kwargs={"collection_code": self.instance.code},
            )
            extra_help_text = " URL: {}".format(self.instance.journal.site_url(path))
            self.fields["code"].help_text += extra_help_text

    class Meta:
        model = models.Issue
        fields = (
            'issue_title', 'volume', 'issue', 'date', 'issue_description',
            'short_description', 'cover_image', 'large_image', 'issue_type',
            'code', 'doi', 'isbn',
        )


class IssueGalleyForm(core_forms.FileUploadForm):
    MIMETYPES = files.PDF_MIMETYPES

    def __init__(self, *args, **kwargs):
        super().__init__(*args, mimetypes=self.MIMETYPES, **kwargs)


class SortForm(forms.Form):
    sort_field = forms.ChoiceField(
        choices=(
            ('first_page', 'First Page'),
            ('date_published', 'Date Published'),
            ('title', 'Title, Alphabetically'),
            ('article_number', 'Article Number'),
            ('page_numbers', 'Page Numbers (Custom)'),
        )
    )
    order = forms.ChoiceField(
        choices=(
            ('dsc', 'Descending'),
            ('asc', 'Ascending'),
        )
    )
