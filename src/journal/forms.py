__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django import forms
from django.conf import settings
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe

from tinymce.widgets import TinyMCE

from core import models as core_models
from journal import models as journal_models, logic
from utils.forms import CaptchaForm

SEARCH_SORT_OPTIONS = [
        # Translators: Search order options
        ('relevance', _('Relevance')),
        ('title', _('Titles A-Z')),
        ('-title', _('Titles Z-A')),
        ('-date_published', _('Newest')),
        ('date_published', _('Oldest')),
      ]


class JournalForm(forms.ModelForm):

    class Meta:
        model = journal_models.Journal
        fields = ('code', 'domain')
        help_texts = {
            'domain': 'Using a custom domain requires configuring DNS. '
                'The journal will always be available under the /code path',
        }


class ContactForm(forms.ModelForm, CaptchaForm):

    def __init__(self, *args, **kwargs):
        subject = kwargs.pop('subject', None)
        contacts = kwargs.pop('contacts', None)
        super(ContactForm, self).__init__(*args, **kwargs)

        if subject:
            self.fields['subject'].initial = subject

        if contacts:
            contact_choices = []
            for contact in contacts:
                contact_choices.append([contact.email, '{name}, {role}'.format(name=contact.name, role=contact.role)])
            self.fields['recipient'].widget = forms.Select(choices=contact_choices)

    class Meta:
        model = core_models.Contact
        fields = ('recipient', 'sender', 'subject', 'body')


class ResendEmailForm(forms.Form):
    to = forms.CharField(max_length=1000, help_text='Seperate email addresses with ;')
    subject = forms.CharField(max_length=1000)
    body = forms.CharField(widget=TinyMCE)

    def __init__(self, *args, **kwargs):
        log_entry = kwargs.pop('log_entry')
        super(ResendEmailForm, self).__init__(*args, **kwargs)

        self.fields['to'].initial = ';'.join(log_entry.to)
        self.fields['subject'].initial = log_entry.subject
        self.fields['body'].initial = mark_safe(log_entry.description)


class SearchForm(forms.Form):
    SEARCH_FILTERS = {
        "title",
        "abstract",
        "authors",
        "keywords",
        "full_text",
        "orcid",
    }

    def __init__(self, data=None, *args, **kwargs):
        if data:
            data = {k: v for k, v in data.items()}
        super().__init__(data, *args, **kwargs)
        if not settings.ENABLE_FULL_TEXT_SEARCH:
            self.fields.pop('full_text', None)
            self.fields["sort"].choices = SEARCH_SORT_OPTIONS[1:]

        if self.data and not self.has_filter:
            for search_filter in self.SEARCH_FILTERS:
                self.data[search_filter] = "on"
        self.label_suffix = ''

    article_search = forms.CharField(label=_('Search term'), min_length=3, max_length=100, required=False)
    title = forms.BooleanField(initial=True, label=_('Search Titles'), required=False)
    abstract = forms.BooleanField(initial=True, label=_('Search Abstract'), required=False)
    authors = forms.BooleanField(initial=True, label=_('Search Authors'), required=False)
    keywords = forms.BooleanField(initial=True, label=_("Search Keywords"), required=False)
    full_text = forms.BooleanField(initial=True, label=_("Search Full Text"), required=False)
    orcid = forms.BooleanField(label=_("Search ORCIDs"), required=False)
    sort = forms.ChoiceField(label=_('Sort results by'), widget=forms.Select, choices=SEARCH_SORT_OPTIONS)

    def get_search_filters(self):
        """ Generates a dictionary of search_filters from a search form"""
        return {
            "full_text": self.cleaned_data["full_text"],
            "title": self.cleaned_data["title"],
            "authors": self.cleaned_data["authors"],
            "abstract": self.cleaned_data["abstract"],
            "keywords": self.cleaned_data["keywords"],
            "orcid": self.cleaned_data["orcid"],
        }


    @cached_property
    def has_filter(self):
        """Determines if the user has selected at least one search filter
        :return: Boolean indicating if there are any search filters selected
        """
        return "on" in set(self.data.values())


class IssueDisplayForm(forms.ModelForm):
    class Meta:
        model = journal_models.Journal
        fields = (
            'display_issue_volume',
            'display_issue_number',
            'display_issue_year',
            'display_issue_title',
            'display_article_number',
            'display_article_page_numbers',
            'display_issue_doi',
            'display_issues_grouped_by_decade',
        )
