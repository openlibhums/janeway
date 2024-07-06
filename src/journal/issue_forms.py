__copyright__ = "Copyright 2022 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
from django import forms
from django.urls import reverse

from core import files, forms as core_forms, models as core_models
from journal import models


class NewIssue(forms.ModelForm):
    date_open = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}), required=False)
    date_close = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}), required=False)

    def __init__(self, *args, **kwargs):
        journal = kwargs.pop("journal")
        super().__init__(*args, **kwargs)
        self.fields["issue_type"].queryset = models.IssueType.objects.filter(
            journal=journal)
        editors = core_models.Account.objects.filter(
                accountrole__role__slug__in=["editor", "section-editor"],
                accountrole__journal=journal,
        )
        self.fields["managing_editors"].queryset = editors
        self.instance.journal = journal
        if self.instance and self.instance.code:
            path = reverse(
                "journal_collection_by_code_with_digits",
                kwargs={"collection_code": self.instance.code},
            )
            extra_help_text = " URL: {}".format(self.instance.journal.site_url(path))
            self.fields["code"].help_text += extra_help_text

    class Meta:
        model = models.Issue
        fields = (
            'issue_title', 'volume', 'issue', 'date', 'issue_description',
            'short_description', 'cover_image', 'large_image', 'issue_type',
            'code', 'doi', 'isbn', 'short_name', 'description', 'date_open', 'date_close', 'invitees',
            'allowed_sections', 'managing_editors', 'documents', 'expected_submissions', 'internal_notes'
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
