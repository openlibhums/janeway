__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
from django import forms

from core import files, forms as core_forms
from journal import models


class NewIssue(forms.ModelForm):
    class Meta:
        model = models.Issue
        fields = ('issue_title', 'volume', 'issue', 'date', 'issue_description', 'cover_image', 'large_image',
                  'issue_type')


class IssueGalleyForm(core_forms.FileUploadForm):
    MIMETYPES = files.PDF_MIMETYPES

    def __init__(self, *args, **kwargs):
        super().__init__(*args, mimetypes=self.MIMETYPES, **kwargs)
